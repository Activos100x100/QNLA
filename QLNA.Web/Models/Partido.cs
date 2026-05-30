namespace QLNA.Web.Models;

public class Partido
{
    public int id { get; set; }
    public int torneo_Id { get; set; }
    public string? equipo_local { get; set; }
    public string? equipo_visitante { get; set; }
    public DateTime fecha { get; set; }
    public int? goles_local_real { get; set; }
    public int? goles_visitante_real { get; set; }
    public Pronostico? pronostico { get; set; }
}
