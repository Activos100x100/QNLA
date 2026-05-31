using Microsoft.AspNetCore.Authorization;
using QNLA.Api.Auth;
using QNLA.Api.Services;

namespace QNLA.Api.Endpoints;

public static class TorneosEndpoints
{
    public static RouteGroupBuilder MapTorneosEndpoints(this RouteGroupBuilder group)
    {
        group.RequireAuthorization();

        group.MapGet("/", async (IRankingService rankingService) =>
        {
            var torneos = await rankingService.GetTorneosActivosAsync();
            return Results.Ok(torneos);
        });

        group.MapGet("/{id:int}/ranking", async (int id, int? limit, ICurrentUser currentUser, IRankingService rankingService) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var ranking = await rankingService.GetRankingAsync(id, limit ?? 50, currentUser.EmpleadoId.Value);
            return Results.Ok(ranking);
        });

        group.MapGet("/{id:int}/partidos", async (int id, bool? solo_pendientes, IRankingService rankingService) =>
        {
            var partidos = await rankingService.GetPartidosAsync(id, solo_pendientes ?? true);
            return Results.Ok(partidos);
        });

        group.MapGet("/{id:int}/grupos", async (int id, IRankingService rankingService) =>
        {
            var partidos = await rankingService.GetGruposAsync(id);
            return Results.Ok(partidos);
        }); 

        group.MapPost("/{id:int}/calcular-puntos/{partidoId:int}", [Authorize] async (int partidoId, IRankingService rankingService) =>
        {
            var updated = await rankingService.CalcularPuntosPartidoAsync(partidoId);
            return Results.Ok(new { updated });
        });

        return group;
    }
}
