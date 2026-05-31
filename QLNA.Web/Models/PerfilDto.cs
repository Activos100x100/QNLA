namespace QLNA.Web.Models;

public class PerfilDto
{
    public int usuario_id { get; set; }
    public string? nombre { get; set; }
    public string? alias { get; set; }
    public string? email { get; set; }
    public string? telefono { get; set; }
    public int puntos { get; set; }
    public int posicion { get; set; }
}
