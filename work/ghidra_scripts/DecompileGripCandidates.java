// Decompile functions that compare with the shared 0.1f constant near vehicle physics.
//@category Trackmania

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class DecompileGripCandidates extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] addresses = getScriptArgs();
        if (addresses.length == 0) {
            addresses = new String[] {
                "140846dc0", "140847940", "14084da80", "14084f1a0",
                "14085ad30", "140869cd0", "14086b060", "14086bc50",
                "14082e9c0", "14072b7b0"
            };
        }
        File directory = new File("ghidra_decompiled");
        directory.mkdirs();
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        try {
            for (String address : addresses) {
                Function function = getFunctionContaining(toAddr("0x" + address));
                File output = new File(directory, address + ".c");
                try (PrintWriter writer = new PrintWriter(new FileWriter(output))) {
                    if (function == null) {
                        writer.println("No function at " + address);
                        continue;
                    }
                    writer.println("// " + function.getName() + " at " + function.getEntryPoint());
                    writer.println("// size " + function.getBody().getNumAddresses());
                    DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
                    if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
                        writer.println(result.getDecompiledFunction().getC());
                    }
                    else {
                        writer.println("Decompilation failed: " + result.getErrorMessage());
                    }
                }
                println("Wrote " + output.getName());
            }
        }
        finally {
            decompiler.dispose();
        }
    }
}
