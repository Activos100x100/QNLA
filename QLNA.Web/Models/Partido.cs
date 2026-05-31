using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Partido
{
    [JsonPropertyName("id")]
    public int id { get; set; }
    [JsonPropertyName("torneo_id")]
    public int torneo_id { get; set; }
    [JsonPropertyName("fase_id")]
    public int? fase_id { get; set; }
    [JsonPropertyName("grupo_id")]
    public int? grupo_id { get; set; }
    public int? sede_id { get; set; }
    public int seleccion_local_id { get; set; }
    public int seleccion_visitante_id { get; set; }
    [JsonPropertyName("seleccion_local")]
    public string? seleccion_local_nombre { get; set; }
    [JsonPropertyName("seleccion_visitante")]
    public string? seleccion_visitante_nombre { get; set; }
    [JsonPropertyName("fecha_partido")]
    public DateTime fecha_partido { get; set; }
    [JsonPropertyName("cierre_pronostico")]
    public DateTime? cierre_pronostico { get; set; }
    [JsonPropertyName("goles_local")]
    public int? goles_local { get; set; }
    [JsonPropertyName("goles_visitante")]
    public int? goles_visitante { get; set; }
    [JsonPropertyName("finalizado")]
    public bool finalizado { get; set; }

    [JsonIgnore]
    public Pronostico? pronostico { get; set; }

    public int torneo_Id => torneo_id;
    public string? equipo_local => seleccion_local_nombre;
    public string? equipo_visitante => seleccion_visitante_nombre;
    public DateTime fecha => fecha_partido;
    public int? goles_local_real => finalizado ? goles_local : null;
    public int? goles_visitante_real => finalizado ? goles_visitante : null;
}
