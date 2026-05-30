namespace QLNA.Web.Models;

public class Grupo
{
    public int id { get; set; }
    public string? nombre { get; set; }
    public List<Partido>? partidos { get; set; }
}
