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

public sealed record PronosticoItemDto(
    int Id,
    int Partido_Id,
    DateTime Fecha_Partido,
    DateTime Cierre_Pronostico,
    string? Seleccion_Local,
    string? Seleccion_Visitante,
    int Goles_Local,
    int Goles_Visitante,
    int? Puntos_Obtenidos);

public sealed record TorneoDto(
    int Id,
    string Nombre,
    int? Anio,
    bool Activo,
    DateTime? Cierre_Inscripcion,
    DateOnly? Fecha_Inicio,
    DateOnly? Fecha_Fin);

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
    int Posicion,
    int Torneo_Id,
    int Participante_Id,
    int Empleado_Id,
    string? Nombre_Completo,
    string? Alias,
    int Pronosticos_Realizados,
    int Aciertos_Exactos,
    int Aciertos_Ganador,
    int Puntos_Totales);

public sealed record RankingResponse(
    IReadOnlyList<RankingRowDto> Top,
    RankingRowDto? Mi_Posicion);
