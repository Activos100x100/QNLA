namespace QLNA.Web.Models;

public class LoginResponse
{
    public string? access_token { get; set; }
    public string? refresh_token { get; set; }
    public int? usuario_id { get; set; }
    public string? nombre { get; set; }
    public string? email { get; set; }
    public LoginUsuarioDto? usuario { get; set; }
}

public class LoginUsuarioDto
{
    public int? usuario_id { get; set; }
    public int? empleado_id { get; set; }
    public string? nombre { get; set; }
    public string? email { get; set; }
}
