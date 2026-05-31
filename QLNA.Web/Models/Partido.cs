using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Partido
{
    [JsonPropertyName("id")]
    public int id { get; set; }
    [JsonPropertyName("torneo_Id")]
    public int torneo_id { get; set; }
    [JsonPropertyName("fase_Id")]
    public int? fase_id { get; set; }
    [JsonPropertyName("grupo_Id")]
    public int? grupo_id { get; set; }
    public int? sede_id { get; set; }
    public int seleccion_local_id { get; set; }
    public int seleccion_visitante_id { get; set; }
    [JsonPropertyName("seleccion_Local")]
    public string? seleccion_local_nombre { get; set; }
    [JsonPropertyName("seleccion_Visitante")]
    public string? seleccion_visitante_nombre { get; set; }
    [JsonPropertyName("fecha_Partido")]
    public DateTime fecha_partido { get; set; }
    [JsonPropertyName("cierre_Pronostico")]
    public DateTime? cierre_pronostico { get; set; }
    [JsonPropertyName("goles_Local")]
    public int? goles_local { get; set; }
    [JsonPropertyName("goles_Visitante")]
    public int? goles_visitante { get; set; }
    [JsonPropertyName("finalizado")]
    public bool finalizado { get; set; }

    [JsonIgnore]
    public Pronostico? pronostico { get; set; }

    [JsonIgnore]
    public int torneo_Id => torneo_id;
    [JsonIgnore]
    public string? equipo_local => seleccion_local_nombre;
    [JsonIgnore]
    public string? equipo_visitante => seleccion_visitante_nombre;
    [JsonIgnore]
    public DateTime fecha => fecha_partido;
    [JsonIgnore]
    public int? goles_local_real => finalizado ? goles_local : null;
    [JsonIgnore]
    public int? goles_visitante_real => finalizado ? goles_visitante : null;
}
