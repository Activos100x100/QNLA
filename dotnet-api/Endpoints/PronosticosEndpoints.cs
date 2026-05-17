using Microsoft.AspNetCore.Authorization;
using QNLA.Api.Auth;
using QNLA.Api.Models;
using QNLA.Api.Services;

namespace QNLA.Api.Endpoints;

public static class PronosticosEndpoints
{
    public static RouteGroupBuilder MapPronosticosEndpoints(this RouteGroupBuilder group)
    {
        group.RequireAuthorization();

        group.MapPost("/", async (PronosticoUpsertRequest request, ICurrentUser currentUser, IPronosticoService service) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var (statusCode, payload) = await service.UpsertPronosticoAsync(currentUser.EmpleadoId.Value, request);
            return Results.Json(payload, statusCode: statusCode);
        });

        group.MapPut("/{id:int}", async (int id, PronosticoUpdateRequest request, ICurrentUser currentUser, IPronosticoService service) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var (statusCode, payload) = await service.UpdatePronosticoAsync(currentUser.EmpleadoId.Value, id, request);
            return Results.Json(payload, statusCode: statusCode);
        });

        group.MapGet("/mios", async (int torneo_id, ICurrentUser currentUser, IPronosticoService service) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var rows = await service.GetMisPronosticosAsync(currentUser.EmpleadoId.Value, torneo_id);
            return Results.Ok(rows);
        });

        group.MapDelete("/{id:int}", async (int id, ICurrentUser currentUser, IPronosticoService service) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var (statusCode, payload) = await service.DeletePronosticoAsync(currentUser.EmpleadoId.Value, id);
            return Results.Json(payload, statusCode: statusCode);
        });

        return group;
    }
}
