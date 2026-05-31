namespace QLNA.Web.Models;

public class RankingResponseDto
{
    public List<RankingEntryDto> entradas { get; set; } = new();
    public int? mi_posicion { get; set; }
    public int? mis_puntos { get; set; }
    public List<RankingEntryDto>? top { get; set; }
    public RankingEntryDto? mi_posicion_detalle { get; set; }
}

public class RankingEntryDto
{
    public int posicion { get; set; }
    public int? participante_id { get; set; }
    public int? usuario_id { get; set; }
    public int? empleado_id { get; set; }
    public string? nombre { get; set; }
    public string? alias { get; set; }
    public string? email { get; set; }
    public int puntos_totales { get; set; }
    public int aciertos_exactos { get; set; }
    public int aciertos_ganador { get; set; }
    public int partidos_pronosticados { get; set; }

    public int puntos => puntos_totales;
}
