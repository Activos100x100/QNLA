namespace QLNA.Web.Models;

public class Pronostico
{
    public int id { get; set; }
    public int partido_id { get; set; }
    public int? goles_local { get; set; }
    public int? goles_visitante { get; set; }
}
