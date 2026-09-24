using System.Globalization;
using GBX.NET;
using GBX.NET.Engines.Game;
using GBX.NET.Engines.Scene;
using GBX.NET.LZO;
using GBX.NET.ZLib;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
if (args.Length != 2)
{
    Console.Error.WriteLine("Usage: FlixInspect <map.Map.Gbx> <run.Ghost.gbx>");
    return;
}

Gbx.LZO = new Lzo();
Gbx.ZLib = new ZLib();

var map = Gbx.ParseNode<CGameCtnChallenge>(args[0]);
Console.WriteLine($"Map: {map.MapName}");
Console.WriteLine($"Plastic blocks: {map.GetBlocks().Count(block => block.Name.Contains("Plastic"))}");

var ghost = Gbx.ParseNode<CGameCtnGhost>(args[1]);
Console.WriteLine($"Ghost time: {ghost.RaceTime}");
var vehicle = ghost.RecordData?.EntList.FirstOrDefault(
    entity => entity.Samples.Count > 0 &&
              entity.Samples[0] is CSceneVehicleVis.EntRecordDelta);
if (vehicle is null)
{
    Console.Error.WriteLine("No vehicle telemetry in ghost");
    return;
}

Console.WriteLine($"Vehicle samples: {vehicle.Samples.Count}");
string? previousMaterials = null;
bool? previousGround = null;
foreach (var raw in vehicle.Samples)
{
    var sample = (CSceneVehicleVis.EntRecordDelta)raw;
    var materials = $"{sample.FLGroundContactMaterial}/{sample.FRGroundContactMaterial}/{sample.RLGroundContactMaterial}/{sample.RRGroundContactMaterial}";
    if (materials != previousMaterials || sample.IsGroundContact != previousGround)
    {
        Console.WriteLine($"{sample.Time} materials={materials} " +
            $"ice={sample.FLIcing:F3}/{sample.FRIcing:F3}/{sample.RLIcing:F3}/{sample.RRIcing:F3} " +
            $"ground={sample.IsGroundContact} steer={sample.Steer:F3} speed={sample.Speed:F2}");
    }
    previousMaterials = materials;
    previousGround = sample.IsGroundContact;
}
