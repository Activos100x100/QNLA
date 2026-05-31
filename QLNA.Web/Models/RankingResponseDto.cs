using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class RankingResponseDto
{
    [JsonPropertyName("entradas")]
    public List<RankingEntryDto> entradas { get; set; } = new();
    [JsonIgnore]
    public int? mi_posicion { get; set; }
    [JsonIgnore]
    public int? mis_puntos { get; set; }
    [JsonPropertyName("top")]
    public List<RankingEntryDto>? top { get; set; }
    [JsonPropertyName("mi_posicion")]
    public RankingEntryDto? mi_posicion_detalle { get; set; }
}

public class RankingEntryDto
{
    [JsonPropertyName("posicion")]
    public int posicion { get; set; }
    [JsonPropertyName("participante_id")]
    public int? participante_id { get; set; }
    public int? usuario_id { get; set; }
    [JsonPropertyName("empleado_id")]
    public int? empleado_id { get; set; }
    [JsonPropertyName("nombre_completo")]
    public string? nombre { get; set; }
    [JsonPropertyName("alias")]
    public string? alias { get; set; }
    public string? email { get; set; }
    [JsonPropertyName("puntos_totales")]
    public int puntos_totales { get; set; }
    [JsonPropertyName("aciertos_exactos")]
    public int aciertos_exactos { get; set; }
    [JsonPropertyName("aciertos_ganador")]
    public int aciertos_ganador { get; set; }
    [JsonPropertyName("pronosticos_realizados")]
    public int partidos_pronosticados { get; set; }

    public int puntos => puntos_totales;
}
