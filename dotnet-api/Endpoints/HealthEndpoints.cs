namespace QNLA.Api.Endpoints;

public static class HealthEndpoints
{
    public static IEndpointRouteBuilder MapHealthEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapGet("/health", () => Results.Ok(new { status = "ok" })).AllowAnonymous();
        app.MapGet("/health/ready", () => Results.Ok(new { status = "ready" })).AllowAnonymous();
        app.MapGet("/health/version", () => Results.Ok(new { version = "1.0.0" })).AllowAnonymous();
        return app;
    }
}
