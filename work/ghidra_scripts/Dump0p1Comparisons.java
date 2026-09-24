// Show instruction flow around every direct 0.1f comparison.
//@category Trackmania

import java.io.FileWriter;
import java.io.PrintWriter;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;

public class Dump0p1Comparisons extends GhidraScript {
    @Override
    public void run() throws Exception {
        String path = "ghidra_0p1_comparisons.txt";
        try (PrintWriter out = new PrintWriter(new FileWriter(path))) {
            for (Reference ref : getReferencesTo(toAddr("0x141d1ef7c"))) {
                Address source = ref.getFromAddress();
                Instruction instruction = getInstructionAt(source);
                if (instruction == null || !instruction.getMnemonicString().contains("COMISS")) continue;
                Function function = getFunctionContaining(source);
                out.printf("%n=== %s in %s ===%n", source,
                    function == null ? "none" : function.getName() + "@" + function.getEntryPoint());
                Instruction first = instruction;
                for (int i = 0; i < 14; i++) {
                    Instruction previous = getInstructionBefore(first);
                    if (previous == null || (function != null && !function.getBody().contains(previous.getAddress()))) break;
                    first = previous;
                }
                Instruction next = first;
                for (int i = 0; i < 23 && next != null; i++) {
                    if (function != null && !function.getBody().contains(next.getAddress())) break;
                    out.printf("%s  %s%n", next.getAddress(), next);
                    next = getInstructionAfter(next);
                }
            }
        }
        println("Wrote " + path);
    }
}
