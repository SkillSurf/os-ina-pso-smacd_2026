v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -120 -70 -120 -30 {lab=V_CMFB}
N -360 -90 -360 -50 {lab=#net1}
N -170 50 -120 50 {lab=#net2}
N -170 0 -120 0 {lab=#net2}
N -170 0 -170 50 {lab=#net2}
N -360 50 -310 50 {lab=#net2}
N -360 0 -310 0 {lab=#net2}
N -310 0 -310 50 {lab=#net2}
N -360 80 -130 80 {lab=#net2}
N -360 30 -360 80 {lab=#net2}
N -120 30 -120 80 {lab=#net2}
N -130 80 -120 80 {lab=#net2}
N -240 80 -240 120 {lab=#net2}
N -290 200 -240 200 {lab=VSS}
N -290 150 -240 150 {lab=VSS}
N -290 150 -290 200 {lab=VSS}
N 120 -70 120 -30 {lab=V_CMFB}
N 120 50 170 50 {lab=#net3}
N 120 0 170 0 {lab=#net3}
N 170 0 170 50 {lab=#net3}
N 310 50 360 50 {lab=#net3}
N 310 0 360 0 {lab=#net3}
N 310 0 310 50 {lab=#net3}
N 130 80 360 80 {lab=#net3}
N 360 30 360 80 {lab=#net3}
N 120 30 120 80 {lab=#net3}
N 120 80 130 80 {lab=#net3}
N 240 80 240 120 {lab=#net3}
N 240 200 290 200 {lab=VSS}
N 240 150 290 150 {lab=VSS}
N 290 150 290 200 {lab=VSS}
N 240 180 240 210 {lab=VSS}
N 240 210 240 220 {lab=VSS}
N -80 0 80 0 {lab=V_CM}
N -240 180 -240 220 {lab=VSS}
N -240 220 -240 240 {lab=VSS}
N -240 240 240 240 {lab=VSS}
N 240 220 240 240 {lab=VSS}
N -120 -70 120 -70 {lab=V_CMFB}
N -360 -160 -310 -160 {lab=VDD}
N -360 -210 -310 -210 {lab=VDD}
N -310 -210 -310 -160 {lab=VDD}
N -360 -130 -360 -90 {lab=#net1}
N -440 -100 -360 -100 {lab=#net1}
N -440 -160 -440 -100 {lab=#net1}
N -440 -160 -400 -160 {lab=#net1}
N -360 -240 -360 -190 {lab=VDD}
N 0 -160 50 -160 {lab=VDD}
N 0 -210 50 -210 {lab=VDD}
N 50 -210 50 -160 {lab=VDD}
N 0 -130 0 -90 {lab=V_CMFB}
N -80 -100 0 -100 {lab=V_CMFB}
N -80 -160 -80 -100 {lab=V_CMFB}
N -80 -160 -40 -160 {lab=V_CMFB}
N 0 -240 0 -190 {lab=VDD}
N 0 -90 0 -70 {lab=V_CMFB}
N -360 -240 0 -240 {lab=VDD}
N -360 -50 -360 -30 {lab=#net1}
N 360 -90 360 -50 {lab=#net4}
N 310 -160 360 -160 {lab=VDD}
N 310 -210 360 -210 {lab=VDD}
N 310 -210 310 -160 {lab=VDD}
N 360 -130 360 -90 {lab=#net4}
N 360 -100 440 -100 {lab=#net4}
N 440 -160 440 -100 {lab=#net4}
N 400 -160 440 -160 {lab=#net4}
N 360 -240 360 -190 {lab=VDD}
N 360 -50 360 -30 {lab=#net4}
N 0 -240 360 -240 {lab=VDD}
N -200 150 200 150 {lab=V_B2}
N -120 -160 -80 -160 {lab=V_CMFB}
N -420 0 -400 0 {lab=V_OP}
N -430 0 -420 0 {lab=V_OP}
N 400 0 420 0 {lab=V_ON}
N 0 0 0 20 {lab=V_CM}
N 0 150 0 170 {lab=V_B2}
N 240 240 360 240 {lab=VSS}
N -430 -240 -360 -240 {lab=VDD}
N -410 140 -410 160 {lab=V_B2}
N -410 220 -410 240 {lab=VSS}
N -510 140 -510 160 {lab=V_CM}
N -510 220 -510 240 {lab=VSS}
N -510 240 -240 240 {lab=VSS}
C {sky130_fd_pr/nfet_01v8.sym} -380 0 0 0 {name=MN1
W=\{W_7\}
L=\{L_7\}
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
C {sky130_fd_pr/nfet_01v8.sym} -100 0 0 1 {name=MN2
W=\{W_7\}
L=\{L_7\}
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
C {sky130_fd_pr/nfet_01v8.sym} -220 150 0 1 {name=MN7
W=\{W_5\}
L=\{L_5\}
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
C {sky130_fd_pr/nfet_01v8.sym} 380 0 0 1 {name=MN6
W=\{W_7\}
L=\{L_7\}
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
C {sky130_fd_pr/nfet_01v8.sym} 100 0 0 0 {name=MN5
W=\{W_7\}
L=\{L_7\}
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
C {sky130_fd_pr/nfet_01v8.sym} 220 150 0 0 {name=MN8
W=\{W_5\}
L=\{L_5\}
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
C {sky130_fd_pr/pfet_01v8.sym} -380 -160 0 0 {name=MP9
W=\{W_8\}/2
L=\{L_8\}
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
C {sky130_fd_pr/pfet_01v8.sym} -20 -160 0 0 {name=MP13
W=\{W_8\}
L=\{L_8\}
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
C {sky130_fd_pr/pfet_01v8.sym} 380 -160 0 1 {name=MP10
W=\{W_8\}/2
L=\{L_8\}
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
C {opin.sym} -120 -160 0 1 {name=p11 lab=V_CMFB}
C {ipin.sym} -430 0 0 0 {name=p5 lab=V_OP}
C {ipin.sym} 420 0 2 0 {name=p1 lab=V_ON}
C {lab_pin.sym} 0 20 3 0 {name=p14 sig_type=std_logic lab=V_CM}
C {lab_pin.sym} 0 170 3 0 {name=p2 sig_type=std_logic lab=V_B2}
C {iopin.sym} 360 240 2 1 {name=p13 lab=VSS}
C {iopin.sym} -430 -240 0 1 {name=p3 lab=VDD}
C {devices/vsource.sym} -410 190 0 0 {name=V2 value=\{V_B2\} }
C {lab_pin.sym} -410 140 3 1 {name=p12 sig_type=std_logic lab=V_B2}
C {devices/vsource.sym} -510 190 0 0 {name=V1 value=\{V_CM\} }
C {lab_pin.sym} -510 140 3 1 {name=p15 sig_type=std_logic lab=V_CM}
