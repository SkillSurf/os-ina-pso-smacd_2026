v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -120 30 -120 80 {lab=Vc}
N 120 30 120 80 {lab=Vc}
N -120 80 120 80 {lab=Vc}
N 80 0 120 0 {lab=Vc}
N 80 0 80 50 {lab=Vc}
N 80 50 120 50 {lab=Vc}
N -120 0 -80 0 {lab=Vc}
N -80 0 -80 50 {lab=Vc}
N -120 50 -80 50 {lab=Vc}
N 120 -70 120 -30 {lab=Vout}
N -120 -70 -120 -30 {lab=Vx}
N -120 -180 120 -180 {lab=VDD}
N 0 80 0 100 {lab=Vc}
N 0 160 0 180 {lab=VSS}
N 0 -210 0 -180 {lab=VDD}
N -190 0 -160 0 {lab=Vip}
N 160 0 190 0 {lab=Vin}
N -160 -100 -120 -100 {lab=VDD}
N -160 -150 -160 -100 {lab=VDD}
N -160 -150 -120 -150 {lab=VDD}
N -120 -180 -120 -130 {lab=VDD}
N 120 -100 160 -100 {lab=VDD}
N 160 -150 160 -100 {lab=VDD}
N 120 -150 160 -150 {lab=VDD}
N 120 -180 120 -130 {lab=VDD}
N -80 -100 80 -100 {lab=Vx}
N -0 -100 -0 -50 {lab=Vx}
N -120 -50 -0 -50 {lab=Vx}
N 120 -50 190 -50 {lab=Vout}
N 0 -210 20 -210 {lab=VDD}
N -0 180 20 180 {lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} -140 0 0 0 {name=M1
W=\{W_1\}
L=\{L_1\}
nf=1 
mult=1
ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')"
pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')"
as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')"
ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')"
nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')"
sa=0 sb=0 sd=0
model=nfet_01v8
spiceprefix=X
}
C {sky130_fd_pr/nfet_01v8.sym} 140 0 0 1 {name=M2
W=\{W_1\}
L=\{L_1\}
nf=1 
mult=1
ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')"
pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')"
as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')"
ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')"
nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')"
sa=0 sb=0 sd=0
model=nfet_01v8
spiceprefix=X
}
C {isource.sym} 0 130 0 0 {name=I0 value=\{ID\}}
C {devices/code.sym} 330 -70 0 0 {name=TT_MODELS
only_toplevel=true
format="tcleval( @value )"
value="
** opencircuitdesign pdks install
.lib $::SKYWATER_MODELS/sky130.lib.spice tt
"
spice_ignore=false}
C {lab_pin.sym} 0 80 1 0 {name=p2 sig_type=std_logic lab=Vc}
C {sky130_fd_pr/pfet_01v8.sym} -100 -100 0 1 {name=M3
W=\{W_2\}
L=\{L_2\}
nf=1
mult=1
ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')"
pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')"
as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')"
ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')"
nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')"
sa=0 sb=0 sd=0
model=pfet_01v8
spiceprefix=X
}
C {sky130_fd_pr/pfet_01v8.sym} 100 -100 0 0 {name=M4
W=\{W_2\}
L=\{L_2\}
nf=1
mult=1
ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')"
pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')"
as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')"
ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')"
nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')"
sa=0 sb=0 sd=0
model=pfet_01v8
spiceprefix=X
}
C {lab_pin.sym} -120 -50 0 0 {name=p1 sig_type=std_logic lab=Vx}
C {ipin.sym} 190 0 2 0 {name=p6 lab=Vin}
C {ipin.sym} -190 0 2 1 {name=p3 lab=Vip}
C {opin.sym} 190 -50 0 0 {name=p5 lab=Vout}
C {iopin.sym} 20 -210 0 0 {name=p4 lab=VDD}
C {iopin.sym} 20 180 0 0 {name=p7 lab=VSS}
