// Print direct call sites and owning functions for selected vehicle physics functions.
//@category Trackmania

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class InspectCallers extends GhidraScript {
    @Override
    public void run() throws Exception {
        for (String value : getScriptArgs()) {
            Address target = toAddr("0x" + value);
            println("TARGET " + value);
            for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(target)) {
                Function function = getFunctionContaining(ref.getFromAddress());
                println(ref.getFromAddress() + " " + ref.getReferenceType() + " in "
                        + (function == null ? "unknown" : function.getName() + "@" + function.getEntryPoint()));
            }
        }
    }
}
