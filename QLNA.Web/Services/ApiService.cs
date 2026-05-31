using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using QLNA.Web.Models;

namespace QLNA.Web.Services;

public class ApiService
{
    private readonly HttpClient _client;
    private readonly SessionTokenStore _sessionTokenStore;
    private readonly JsonSerializerOptions _jsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public LoginResponse? UsuarioActual { get; private set; }

    public ApiService(HttpClient client, SessionTokenStore sessionTokenStore)
    {
        _client = client;
        _sessionTokenStore = sessionTokenStore;
    }

    public async Task<string> GetHealthAsync()
    {
        try
        {
            return await _client.GetStringAsync("/health");
        }
        catch
        {
            return "unavailable";
        }
    }

    public async Task<bool> LoginAsync(string dni, string password)
    {
        try
        {
            var payload = new LoginRequest { dni_nie = dni, password = password };
            var response = await _client.PostAsJsonAsync("/api/v1/auth/login", payload, _jsonOptions);
            if (!response.IsSuccessStatusCode)
            {
                return false;
            }

            var body = await response.Content.ReadFromJsonAsync<LoginResponse>(_jsonOptions);
            if (body is null || string.IsNullOrWhiteSpace(body.access_token))
            {
                return false;
            }

            if (body.usuario_id is null)
            {
                body.usuario_id = body.usuario?.usuario_id ?? body.usuario?.empleado_id;
            }

            if (string.IsNullOrWhiteSpace(body.nombre))
            {
                body.nombre = body.usuario?.nombre;
            }

            UsuarioActual = body;
            return true;
        }
        catch
        {
            return false;
        }
    }

    public async Task<IEnumerable<Torneo>> GetTorneosAsync()
    {
        try
        {
            var req = await CreateRequestAsync(HttpMethod.Get, "/api/v1/torneos");
            using var res = await _client.SendAsync(req);
            if (!res.IsSuccessStatusCode)
            {
                return Enumerable.Empty<Torneo>();
            }

            return await res.Content.ReadFromJsonAsync<IEnumerable<Torneo>>(_jsonOptions) ?? Enumerable.Empty<Torneo>();
        }
        catch
        {
            return Enumerable.Empty<Torneo>();
        }
    }

    public async Task<IEnumerable<Partido>> GetPartidosAsync(int torneoId)
    {
        try
        {
            var req = await CreateRequestAsync(HttpMethod.Get, $"/api/v1/torneos/{torneoId}/partidos");
            using var res = await _client.SendAsync(req);
            if (!res.IsSuccessStatusCode)
            {
                return Enumerable.Empty<Partido>();
            }

            var partidos = await res.Content.ReadFromJsonAsync<IEnumerable<Partido>>(_jsonOptions) ?? Enumerable.Empty<Partido>();
            foreach (var p in partidos)
            {
                p.pronostico ??= new Pronostico { partido_id = p.id };
            }

            return partidos;
        }
        catch
        {
            return Enumerable.Empty<Partido>();
        }
    }

    public async Task<bool> GuardarPronosticoAsync(Partido partido)
    {
        try
        {
            if (partido.pronostico?.goles_local is null || partido.pronostico?.goles_visitante is null)
            {
                return false;
            }

            var payload = new
            {
                torneo_id = partido.torneo_Id,
                partido_id = partido.id,
                goles_local = partido.pronostico.goles_local.Value,
                goles_visitante = partido.pronostico.goles_visitante.Value
            };

            HttpResponseMessage res;
            if (partido.pronostico.id > 0)
            {
                var req = await CreateRequestAsync(HttpMethod.Put, $"/api/v1/pronosticos/{partido.pronostico.id}", payload);
                res = await _client.SendAsync(req);
            }
            else
            {
                var req = await CreateRequestAsync(HttpMethod.Post, "/api/v1/pronosticos", payload);
                res = await _client.SendAsync(req);
            }

            return res.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<IReadOnlyDictionary<int, Pronostico>> GetPronosticosByTorneoAsync(int torneoId)
    {
        var routes = new[]
        {
            $"/api/v1/pronosticos/usuario/{torneoId}",
            $"/api/v1/torneos/{torneoId}/pronosticos",
            $"/api/v1/pronosticos/torneo/{torneoId}",
            $"/api/v1/pronosticos/{torneoId}",
            $"/api/v1/pronosticos/mios?torneo_id={torneoId}"
        };

        foreach (var route in routes)
        {
            try
            {
                var req = await CreateRequestAsync(HttpMethod.Get, route);
                using var res = await _client.SendAsync(req);
                if (!res.IsSuccessStatusCode)
                {
                    continue;
                }

                var raw = await res.Content.ReadAsStringAsync();
                var parsed = ParsePronosticosDictionary(raw);
                if (parsed.Count > 0)
                {
                    return parsed;
                }
            }
            catch
            {
                // Try next route
            }
        }

        return new Dictionary<int, Pronostico>();
    }

    public async Task<IEnumerable<Grupo>> GetGruposAsync(int torneoId)
    {
        try
        {
            var req = await CreateRequestAsync(HttpMethod.Get, $"/api/v1/torneos/{torneoId}/grupos");
            using var res = await _client.SendAsync(req);
            if (!res.IsSuccessStatusCode)
            {
                return Enumerable.Empty<Grupo>();
            }

            return await res.Content.ReadFromJsonAsync<IEnumerable<Grupo>>(_jsonOptions) ?? Enumerable.Empty<Grupo>();
        }
        catch
        {
            return Enumerable.Empty<Grupo>();
        }
    }

    public async Task<RankingResponseDto> GetRankingAsync(int torneoId)
    {
        try
        {
            var req = await CreateRequestAsync(HttpMethod.Get, $"/api/v1/torneos/{torneoId}/ranking");
            using var res = await _client.SendAsync(req);
            if (!res.IsSuccessStatusCode)
            {
                return new RankingResponseDto();
            }

            var raw = await res.Content.ReadAsStringAsync();
            var ranking = JsonSerializer.Deserialize<RankingResponseDto>(raw, _jsonOptions) ?? new RankingResponseDto();

            if (ranking.entradas.Count == 0 && ranking.top is { Count: > 0 })
            {
                ranking.entradas = ranking.top.Select(x => new RankingEntryDto
                {
                    posicion = x.posicion,
                    usuario_id = x.usuario_id ?? x.empleado_id,
                    nombre = x.nombre ?? x.nombre_completo ?? x.alias,
                    puntos = x.puntos ?? x.puntos_totales
                }).ToList();
            }

            if (ranking.mi_posicion is null && ranking.mi_posicion_detalle is { } detalle)
            {
                ranking.mi_posicion = detalle.posicion;
                ranking.mis_puntos = detalle.puntos ?? detalle.puntos_totales;
            }

            return ranking;
        }
        catch
        {
            return new RankingResponseDto();
        }
    }

    public async Task<PerfilDto?> GetPerfilAsync(int torneoId)
    {
        try
        {
            var req = await CreateRequestAsync(HttpMethod.Get, $"/api/v1/participante/perfil/{torneoId}");
            using var res = await _client.SendAsync(req);
            if (!res.IsSuccessStatusCode)
            {
                return null;
            }

            return await res.Content.ReadFromJsonAsync<PerfilDto>(_jsonOptions);
        }
        catch
        {
            return null;
        }
    }

    public async Task<PerfilDto?> ActualizarPerfilAsync(int torneoId, ActualizarPerfilRequest request)
    {
        try
        {
            var req = await CreateRequestAsync(HttpMethod.Put, $"/api/v1/participante/perfil/{torneoId}", request);
            using var res = await _client.SendAsync(req);
            if (!res.IsSuccessStatusCode)
            {
                return null;
            }

            return await res.Content.ReadFromJsonAsync<PerfilDto>(_jsonOptions);
        }
        catch
        {
            return null;
        }
    }

    private async Task<HttpRequestMessage> CreateRequestAsync(HttpMethod method, string path, object? body = null)
    {
        var req = new HttpRequestMessage(method, path);
        var token = await _sessionTokenStore.GetAccessTokenAsync();
        if (!string.IsNullOrWhiteSpace(token))
        {
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }

        if (body is not null)
        {
            req.Content = new StringContent(JsonSerializer.Serialize(body, _jsonOptions), Encoding.UTF8, "application/json");
        }

        return req;
    }

    private IReadOnlyDictionary<int, Pronostico> ParsePronosticosDictionary(string raw)
    {
        var result = new Dictionary<int, Pronostico>();
        if (string.IsNullOrWhiteSpace(raw))
        {
            return result;
        }

        try
        {
            using var doc = JsonDocument.Parse(raw);
            var root = doc.RootElement;

            if (root.ValueKind == JsonValueKind.Object)
            {
                if (root.TryGetProperty("pronosticos", out var nested))
                {
                    ParseCollection(nested, result);
                }
                else
                {
                    foreach (var property in root.EnumerateObject())
                    {
                        if (property.Value.ValueKind != JsonValueKind.Object)
                        {
                            continue;
                        }

                        var pron = ParsePronostico(property.Value);
                        if (pron is null)
                        {
                            continue;
                        }

                        var key = pron.partido_id != 0
                            ? pron.partido_id
                            : (int.TryParse(property.Name, out var parsedKey) ? parsedKey : 0);

                        if (key != 0)
                        {
                            pron.partido_id = key;
                            result[key] = pron;
                        }
                    }
                }
            }
            else if (root.ValueKind == JsonValueKind.Array)
            {
                ParseCollection(root, result);
            }
        }
        catch
        {
            // Ignore invalid payloads
        }

        return result;
    }

    private void ParseCollection(JsonElement collection, IDictionary<int, Pronostico> result)
    {
        if (collection.ValueKind != JsonValueKind.Array)
        {
            return;
        }

        foreach (var item in collection.EnumerateArray())
        {
            var pron = ParsePronostico(item);
            if (pron is not null && pron.partido_id != 0)
            {
                result[pron.partido_id] = pron;
            }
        }
    }

    private Pronostico? ParsePronostico(JsonElement element)
    {
        try
        {
            if (element.ValueKind != JsonValueKind.Object)
            {
                return null;
            }

            if (element.TryGetProperty("pronostico", out var nested) && nested.ValueKind == JsonValueKind.Object)
            {
                element = nested;
            }

            return JsonSerializer.Deserialize<Pronostico>(element.GetRawText(), _jsonOptions);
        }
        catch
        {
            return null;
        }
    }
}
