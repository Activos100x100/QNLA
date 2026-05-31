using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Partido
{
    public int id { get; set; }
    public int torneo_id { get; set; }
    public int? fase_id { get; set; }
    public int? grupo_id { get; set; }
    public int? sede_id { get; set; }
    public int seleccion_local_id { get; set; }
    public int seleccion_visitante_id { get; set; }
    public string? seleccion_local_nombre { get; set; }
    public string? seleccion_visitante_nombre { get; set; }
    public DateTime fecha_partido { get; set; }
    public DateTime? cierre_pronostico { get; set; }
    public int? goles_local { get; set; }
    public int? goles_visitante { get; set; }
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
