package Test;
import AXI4::*;
import AXI4_DelayShim::*;
import BlueBasics::*;
import SourceSink::*;
import Assert::*;
(* synthesize *)
module mkTest(Empty);
    NumProxy#(128) depth=error("proxy");
    AXI4_Shim#(4,32,64,0,0,0,0,0) shim <- mkAXI4_DelayShim(depth,50);
    Reg#(Bit#(32)) cycles <- mkReg(0);
    Reg#(Bit#(4)) sent <- mkReg(0);
    Reg#(Bit#(4)) received <- mkReg(0);
    Reg#(Bool) bSent <- mkReg(False);
    Reg#(Bool) bSeen <- mkReg(False);
    rule tick;
        cycles <= cycles+1;
        dynamicAssert(cycles<100,"AXI delay timeout");
    endrule
    rule send (sent<3);
        AXI4_ARFlit#(4,32,0) ar=unpack(0);
        ar.arid=sent;
        ar.araddr=zeroExtend(sent)<<3;
        shim.slave.ar.put(ar);
        sent<=sent+1;
    endrule
    rule receive;
        let ar <- get(shim.master.ar);
        dynamicAssert(cycles==50+zeroExtend(received),"Read delay or throughput mismatch");
        dynamicAssert(ar.arid==received,"Read ordering mismatch");
        received<=received+1;
    endrule
    rule sendB (!bSent);
        AXI4_BFlit#(4,0) b=unpack(0);
        b.bid=7;
        shim.master.b.put(b);
        bSent<=True;
    endrule
    rule receiveB;
        let b <- get(shim.slave.b);
        dynamicAssert(cycles==50 && b.bid==7,"Write response delay mismatch");
        bSeen<=True;
    endrule
    rule finish (received==3 && bSeen);
        $display("PASS: 50-cycle AR/B delay; three reads accepted and released one per cycle");
        $finish(0);
    endrule
endmodule
endpackage
