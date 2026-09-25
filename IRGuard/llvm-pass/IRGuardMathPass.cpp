#include "llvm/IR/Function.h"
#include "llvm/IR/Instruction.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Operator.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"

#include <cstdlib>
#include <set>
#include <sstream>
#include <string>

using namespace llvm;

namespace {

static std::set<std::string> parsePolicy() {
    std::set<std::string> enabled;

    const char *env = std::getenv("IRGUARD_POLICY");
    if (!env)
        return enabled;

    std::stringstream ss(env);
    std::string token;

    while (std::getline(ss, token, ',')) {
        if (!token.empty())
            enabled.insert(token);
    }

    return enabled;
}


static bool reassociateOneAdd(Function &F) {
    BinaryOperator *Outer = nullptr;
    BinaryOperator *Inner = nullptr;

    for (BasicBlock &BB : F) {
        for (Instruction &I : BB) {
            auto *BO = dyn_cast<BinaryOperator>(&I);
            if (!BO || BO->getOpcode() != Instruction::FAdd)
                continue;

            auto *LHS =
                dyn_cast<BinaryOperator>(BO->getOperand(0));

            if (!LHS ||
                LHS->getOpcode() != Instruction::FAdd ||
                !LHS->hasOneUse())
                continue;

            Outer = BO;
            Inner = LHS;
            break;
        }

        if (Outer)
            break;
    }

    if (!Outer)
        return false;

    Value *A = Inner->getOperand(0);
    Value *B = Inner->getOperand(1);
    Value *C = Outer->getOperand(1);

    auto *BC = BinaryOperator::CreateFAdd(
        B, C, "irguard.bc", Outer
    );

    BC->setHasAllowReassoc(true);

    Outer->setOperand(0, A);
    Outer->setOperand(1, BC);
    Outer->setHasAllowReassoc(true);

    Inner->eraseFromParent();

    return true;
}

class IRGuardMathPass : public PassInfoMixin<IRGuardMathPass> {
public:
    PreservedAnalyses run(Function &F,
                          FunctionAnalysisManager &) {
        auto policy = parsePolicy();

        bool useContract = policy.count("contract");
        bool useReassoc  = policy.count("reassoc");
        bool useArcp     = policy.count("arcp");
        bool useNNaN     = policy.count("nnan");
        bool useNInf     = policy.count("ninf");

        unsigned fpOps = 0;
        unsigned modified = 0;

        for (BasicBlock &BB : F) {
            for (Instruction &I : BB) {
                if (!isa<FPMathOperator>(&I))
                    continue;

                fpOps++;
                bool changed = false;

                if (useNNaN) {
                    I.setHasNoNaNs(true);
                    changed = true;
                }

                if (useNInf) {
                    I.setHasNoInfs(true);
                    changed = true;
                }

                if (useContract &&
                    (I.getOpcode() == Instruction::FMul ||
                     I.getOpcode() == Instruction::FAdd)) {
                    I.setHasAllowContract(true);
                    changed = true;
                }

                if (useReassoc &&
                    (I.getOpcode() == Instruction::FMul ||
                     I.getOpcode() == Instruction::FAdd)) {
                    I.setHasAllowReassoc(true);
                    changed = true;
                }

                if (useArcp &&
                    I.getOpcode() == Instruction::FDiv) {
                    I.setHasAllowReciprocal(true);
                    changed = true;
                }

                if (changed)
                    modified++;
            }
        }

        bool rewrote = false;

        if (useReassoc)
            rewrote = reassociateOneAdd(F);

        errs() << "[IRGuard] function=" << F.getName()
               << " fp_ops=" << fpOps
               << " modified=" << modified
               << " reassociated=" << rewrote
               << " policy=";

        if (policy.empty()) {
            errs() << "none";
        } else {
            bool first = true;

            for (const auto &flag : policy) {
                if (!first)
                    errs() << ",";
                errs() << flag;
                first = false;
            }
        }

        errs() << "\n";

        if (modified == 0)
            return PreservedAnalyses::all();

        return PreservedAnalyses::none();
    }
};

}

extern "C" LLVM_ATTRIBUTE_WEAK
PassPluginLibraryInfo llvmGetPassPluginInfo() {
    return {
        LLVM_PLUGIN_API_VERSION,
        "IRGuardMathPass",
        LLVM_VERSION_STRING,
        [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name,
                   FunctionPassManager &FPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                    if (Name == "irguard-math") {
                        FPM.addPass(IRGuardMathPass());
                        return true;
                    }

                    return false;
                });
        }
    };
}
