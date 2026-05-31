using System.Text.Json.Serialization;

namespace QNLA.Api.Models;

public sealed record LoginRequest(
    [property: JsonPropertyName("dni_nie")] string Dni_Nie,
    [property: JsonPropertyName("password")] string Password);

public sealed record RefreshRequest(
    [property: JsonPropertyName("refresh_token")] string Refresh_Token);

public sealed record UsuarioDto(
    [property: JsonPropertyName("empleado_id")] int Empleado_Id,
    [property: JsonPropertyName("dni_nie")] string Dni_Nie,
    [property: JsonPropertyName("nombre")] string? Nombre,
    [property: JsonPropertyName("apellidos")] string? Apellidos,
    [property: JsonPropertyName("email")] string? Email);

public sealed record LoginResponse(
    [property: JsonPropertyName("access_token")] string Access_Token,
    [property: JsonPropertyName("refresh_token")] string Refresh_Token,
    [property: JsonPropertyName("expires_in")] int Expires_In,
    [property: JsonPropertyName("usuario")] UsuarioDto Usuario);

public sealed record AccessTokenResponse(
    [property: JsonPropertyName("access_token")] string Access_Token,
    [property: JsonPropertyName("expires_in")] int Expires_In);

public sealed record PronosticoUpsertRequest(
    [property: JsonPropertyName("torneo_id")] int Torneo_Id,
    [property: JsonPropertyName("partido_id")] int Partido_Id,
    [property: JsonPropertyName("goles_local")] int Goles_Local,
    [property: JsonPropertyName("goles_visitante")] int Goles_Visitante);

public sealed record PronosticoUpdateRequest(
    [property: JsonPropertyName("goles_local")] int Goles_Local,
    [property: JsonPropertyName("goles_visitante")] int Goles_Visitante);

public sealed class PronosticoItemDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    [JsonPropertyName("partido_id")]
    public int Partido_Id { get; set; }
    [JsonPropertyName("fecha_partido")]
    public DateTime Fecha_Partido { get; set; }
    [JsonPropertyName("cierre_pronostico")]
    public DateTime Cierre_Pronostico { get; set; }
    [JsonPropertyName("seleccion_local")]
    public string? Seleccion_Local { get; set; }
    [JsonPropertyName("seleccion_visitante")]
    public string? Seleccion_Visitante { get; set; }
    [JsonPropertyName("goles_local")]
    public int Goles_Local { get; set; }
    [JsonPropertyName("goles_visitante")]
    public int Goles_Visitante { get; set; }
    [JsonPropertyName("puntos_obtenidos")]
    public int? Puntos_Obtenidos { get; set; }
}

public class TorneoDto
{
    [JsonPropertyName("id")]
    public int Id { get; init; }
    [JsonPropertyName("nombre")]
    public string Nombre { get; init; } = string.Empty;
    [JsonPropertyName("anio")]
    public int Anio { get; init; }
    [JsonPropertyName("activo")]
    public bool Activo { get; init; }
    [JsonPropertyName("cierre_inscripcion")]
    public DateTime Cierre_Inscripcion { get; init; }  // nombre exacto = columna SQL
    [JsonPropertyName("fecha_inicio")]
    public DateTime Fecha_Inicio { get; init; }
    [JsonPropertyName("fecha_fin")]
    public DateTime Fecha_Fin { get; init; }
}

public class GrupoDto
{
    [JsonPropertyName("id")]
    public int Id { get; init; }
    [JsonPropertyName("torneo_id")]
    public int TorneoId { get; init; }
    [JsonPropertyName("nombre")]
    public string Nombre { get; init; } = string.Empty;
}


public sealed record PartidoDto(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("torneo_id")] int Torneo_Id,
    [property: JsonPropertyName("fase_id")] int? Fase_Id,
    [property: JsonPropertyName("grupo_id")] int? Grupo_Id,
    [property: JsonPropertyName("fecha_partido")] DateTime Fecha_Partido,
    [property: JsonPropertyName("cierre_pronostico")] DateTime Cierre_Pronostico,
    [property: JsonPropertyName("seleccion_local")] string? Seleccion_Local,
    [property: JsonPropertyName("seleccion_visitante")] string? Seleccion_Visitante,
    [property: JsonPropertyName("goles_local")] short? Goles_Local,
    [property: JsonPropertyName("goles_visitante")] short? Goles_Visitante,
    [property: JsonPropertyName("finalizado")] bool Finalizado);

public sealed record RankingRowDto(
    [property: JsonPropertyName("posicion")] int Posicion,
    [property: JsonPropertyName("torneo_id")] int Torneo_Id,
    [property: JsonPropertyName("participante_id")] int Participante_Id,
    [property: JsonPropertyName("empleado_id")] int Empleado_Id,
    [property: JsonPropertyName("nombre_completo")] string? Nombre_Completo,
    [property: JsonPropertyName("alias")] string? Alias,
    [property: JsonPropertyName("pronosticos_realizados")] long Pronosticos_Realizados,
    [property: JsonPropertyName("aciertos_exactos")] long Aciertos_Exactos,
    [property: JsonPropertyName("aciertos_ganador")] long Aciertos_Ganador,
    [property: JsonPropertyName("puntos_totales")] long Puntos_Totales);

public sealed record RankingResponse(
    [property: JsonPropertyName("top")] IReadOnlyList<RankingRowDto> Top,
    [property: JsonPropertyName("mi_posicion")] RankingRowDto? Mi_Posicion);

public sealed record UpdateParticipantRequest(
    [property: JsonPropertyName("nombre")] string Nombre,
    [property: JsonPropertyName("alias")] string Alias
);




public sealed record ParticipantDto(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("torneo_id")] int Torneo_Id,
    [property: JsonPropertyName("empleado_id")] int Empleado_Id,
    [property: JsonPropertyName("nombre")] string? Nombre,
    [property: JsonPropertyName("alias")] string? Alias,
    [property: JsonPropertyName("email")] string? Email,
    [property: JsonPropertyName("activo")] bool Activo,
    [property: JsonPropertyName("es_admin")] bool Es_Admin
);