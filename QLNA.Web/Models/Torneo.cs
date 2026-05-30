namespace QLNA.Web.Models;

public class Torneo
{
    public int id { get; set; }
    public string? nombre { get; set; }
    public string? descripcion { get; set; }
    public bool activo { get; set; }
}
