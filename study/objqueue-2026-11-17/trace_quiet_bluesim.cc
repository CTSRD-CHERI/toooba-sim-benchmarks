// Optional link-time trace filter for these Bluesim benchmark models.
// Only $display/$write output changes. No simulation state, $finish, assertion
// control flow, clocks, memory operations or scheduling functions are replaced.
// Validate cycle counts against an unfiltered run before using a new model.
#include "bs_system_tasks.h"
#include <cstdarg>
#include <cstdio>
#include <cstring>

static void output(const char* shape, va_list args) {
    if (!shape || shape[0] != 's') return;
    const std::string* format = va_arg(args, const std::string*);
    if (!format) return;
    const std::string& text = *format;
    if (text.find("mmioPlatform.rl_tohost:") != std::string::npos) {
        // The checked models emit exactly this argument layout.
        if (std::strcmp(shape, "s,32,64,64") != 0) {
            std::fprintf(stderr, "ERROR: unsupported tohost display layout %s\n", shape);
            return;
        }
        const tUInt32 cycles = va_arg(args, tUInt32);
        const tUInt64 value = va_arg(args, tUInt64);
        (void)va_arg(args, tUInt64);
        std::printf("%u: mmioPlatform.rl_tohost: 0x%llx (= %llu)\n",
                    unsigned(cycles), static_cast<unsigned long long>(value),
                    static_cast<unsigned long long>(value));
        std::fflush(stdout);
    } else if (text.find("OBJQ_HIGH") == 0) {
        if (std::strcmp(shape, "s,32,32,32") != 0) {
            std::fprintf(stderr,"ERROR: unsupported OBJQ_HIGH layout %s\n",shape); return;
        }
        unsigned cycle=va_arg(args,tUInt32);
        unsigned used=va_arg(args,tUInt32);
        unsigned limit=va_arg(args,tUInt32);
        std::printf("OBJQ_HIGH cycle=%u used=%u limit=%u\n",cycle,used,limit);
    } else if (text.find("OBJQ_BLOCK") == 0) {
        if (std::strcmp(shape, "s,32,64,32,32,32,32,32") != 0) {
            std::fprintf(stderr,"ERROR: unsupported OBJQ_BLOCK layout %s\n",shape); return;
        }
        unsigned cycle=va_arg(args,tUInt32);
        tUInt64 pc=va_arg(args,tUInt64);
        unsigned lane=va_arg(args,tUInt32);
        unsigned used=va_arg(args,tUInt32);
        unsigned limit=va_arg(args,tUInt32);
        unsigned tail=va_arg(args,tUInt32);
        unsigned load=va_arg(args,tUInt32);
        std::printf("OBJQ_BLOCK cycle=%u pc=0x%llx lane=%u used=%u limit=%u tail=%u load=%u\n",
                    cycle,static_cast<unsigned long long>(pc),lane,used,limit,tail,load);
    } else if (text.find("ASSERT") != std::string::npos ||
               text.find("assertion") != std::string::npos ||
               text.find("ERROR") != std::string::npos ||
               text.find("Error:") != std::string::npos ||
               text.find("FATAL") != std::string::npos ||
               text.find("PANIC") != std::string::npos) {
        // Keep diagnostic templates verbatim. A failing assertion still calls
        // the original, unmodified $finish and is rejected by the runner.
        std::fwrite(text.data(), 1, text.size(), stderr);
        std::fputc('\n', stderr);
    }
}

#define FILTER_TASK(name) \
    void name(tSimStateHdl, Module*, const char* shape, ...) { \
        va_list args; va_start(args, shape); output(shape, args); va_end(args); \
    } \
    void name(tSimStateHdl, Module*) {}

FILTER_TASK(dollar_display)
FILTER_TASK(dollar_displayb)
FILTER_TASK(dollar_displayh)
FILTER_TASK(dollar_displayo)

// FShow emits many tiny $write fragments. Skip those without inspecting or
// formatting their arguments; tohost and assertion diagnostics use $display.
#define SKIP_WRITE(name) \
    void name(tSimStateHdl, Module*, const char*, ...) {} \
    void name(tSimStateHdl, Module*) {}
SKIP_WRITE(dollar_write)
SKIP_WRITE(dollar_writeb)
SKIP_WRITE(dollar_writeh)
SKIP_WRITE(dollar_writeo)
