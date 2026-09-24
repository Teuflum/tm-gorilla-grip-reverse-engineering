// List xrefs to physics strings and the shared 0.1f float constant.
//@category Trackmania

import java.io.FileWriter;
import java.io.PrintWriter;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;

public class InspectPhysicsAnchors extends GhidraScript {
    private PrintWriter out;

    private void describe(String label, String hex) {
        Address address = toAddr("0x" + hex);
        Reference[] refs = getReferencesTo(address);
        out.printf("%n%s at %s: %d references%n", label, address, refs.length);
        for (Reference ref : refs) {
            Address source = ref.getFromAddress();
            Function function = getFunctionContaining(source);
            Instruction instruction = getInstructionAt(source);
            out.printf("  %s  function=%s  instruction=%s%n", source,
                function == null ? "none" : function.getName() + "@" + function.getEntryPoint(),
                instruction == null ? "none" : instruction.toString());
        }
    }

    @Override
    public void run() throws Exception {
        String path = "ghidra_reference_candidates.txt";
        out = new PrintWriter(new FileWriter(path));
        try {
            out.println("Program " + currentProgram.getName());
            describe("PhysicsStep_ProcessContactPoints", "141bea4c8");
            describe("M3to6_AbsorbContact", "141beea70");
            describe("InputSteer", "141be7878");
            describe("Wheels.Elems[0].Icing01", "141be7aa0");
            describe("CPlugVehicleWheelPhyModel", "141bd55e8");
            describe("0.1f", "141d1ef7c");
        }
        finally {
            out.close();
        }
        println("Wrote " + path);
    }
}
