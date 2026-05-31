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
    public int Id { get; set; }
    public int Partido_Id { get; set; }
    public DateTime Fecha_Partido { get; set; }
    public DateTime Cierre_Pronostico { get; set; }
    public string? Seleccion_Local { get; set; }
    public string? Seleccion_Visitante { get; set; }
    public int Goles_Local { get; set; }
    public int Goles_Visitante { get; set; }
    public int? Puntos_Obtenidos { get; set; }
}

public class TorneoDto
{
    public int Id { get; init; }
    public string Nombre { get; init; } = string.Empty;
    public int Anio { get; init; }
    public bool Activo { get; init; }
    public DateTime Cierre_Inscripcion { get; init; }  // nombre exacto = columna SQL
    public DateTime Fecha_Inicio { get; init; }
    public DateTime Fecha_Fin { get; init; }
}

public class GrupoDto
{
    public int Id { get; init; }
    public int TorneoId { get; init; }
    public string Nombre { get; init; } = string.Empty;
}


public sealed record PartidoDto(
    int Id,
    int Torneo_Id,
    int? Fase_Id,
    int? Grupo_Id,
    DateTime Fecha_Partido,
    DateTime Cierre_Pronostico,
    string? Seleccion_Local,
    string? Seleccion_Visitante,
    short? Goles_Local,
    short? Goles_Visitante,
    bool Finalizado);

public sealed record RankingRowDto(
    int Torneo_Id,
    int Participante_Id,
    int Empleado_Id,
    string? Nombre_Completo,
    string? Alias,
    long Pronosticos_Realizados,
    long Aciertos_Exactos,
    long Aciertos_Ganador,
    long Puntos_Totales);

public sealed record RankingResponse(
    IReadOnlyList<RankingRowDto> Top,
    RankingRowDto? Mi_Posicion);

public sealed record UpdateParticipantRequest(
    [property: JsonPropertyName("Nombre")] string Nombre,
    [property: JsonPropertyName("Alias")] string Alias
);




public sealed record ParticipantDto(
    int Id,
    int Torneo_Id,
    int Empleado_Id,
    string? Nombre,
    string? Alias,
    string? Email,
    bool Activo,
    bool Es_Admin
);