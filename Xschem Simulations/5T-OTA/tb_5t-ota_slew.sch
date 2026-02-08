v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -90 30 -90 80 {lab=Vc}
N 90 30 90 80 {lab=Vc}
N -90 80 90 80 {lab=Vc}
N 50 0 90 -0 {lab=Vc}
N 50 0 50 50 {lab=Vc}
N 50 50 90 50 {lab=Vc}
N -90 -0 -50 0 {lab=Vc}
N -50 0 -50 50 {lab=Vc}
N -90 50 -50 50 {lab=Vc}
N 90 -70 90 -30 {lab=Vout}
N -90 -70 -90 -30 {lab=Vx}
N -90 -180 90 -180 {lab=VDD}
N 90 -50 140 -50 {lab=Vout}
N 0 80 0 100 {lab=Vc}
N 0 160 0 180 {lab=GND}
N 0 -200 0 -180 {lab=VDD}
N -210 20 -210 40 {lab=Vip}
N -210 120 -210 140 {lab=GND}
N -210 0 -210 20 {lab=Vip}
N -210 40 -210 60 {lab=Vip}
N -210 0 -130 -0 {lab=Vip}
N 130 0 160 0 {lab=Vout}
N -130 -100 -90 -100 {lab=VDD}
N -130 -150 -130 -100 {lab=VDD}
N -130 -150 -90 -150 {lab=VDD}
N -90 -180 -90 -130 {lab=VDD}
N 90 -100 130 -100 {lab=VDD}
N 130 -150 130 -100 {lab=VDD}
N 90 -150 130 -150 {lab=VDD}
N 90 -180 90 -130 {lab=VDD}
N -50 -100 50 -100 {lab=Vx}
N -0 -100 -0 -50 {lab=Vx}
N -90 -50 -0 -50 {lab=Vx}
N 150 -50 200 -50 {lab=Vout}
N 200 -90 200 -50 {lab=Vout}
N 200 -180 200 -150 {lab=GND}
N 260 -180 260 -150 {lab=GND}
N 200 -180 250 -180 {lab=GND}
N 250 -180 260 -180 {lab=GND}
N 140 -50 150 -50 {lab=Vout}
N 160 -50 160 -0 {lab=Vout}
C {sky130_fd_pr/nfet_01v8.sym} -110 0 0 0 {name=M1
W=W_1
L=L_1
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
C {sky130_fd_pr/nfet_01v8.sym} 110 0 0 1 {name=M2
W=W_1
L=L_1
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
C {isource.sym} 0 130 0 0 {name=I0 value=ID}
C {gnd.sym} 0 180 0 0 {name=l1 lab=GND}
C {vdd.sym} 0 -200 0 0 {name=l2 lab=VDD}
C {lab_pin.sym} 200 -50 0 1 {name=p4 sig_type=std_logic lab=Vout}
C {vsource.sym} -210 90 0 0 {name=Vvip savecurrent=false
value="pulse(1.8 0 0 10p 10p 20u 40u 1)"}
C {lab_pin.sym} -210 0 2 1 {name=p5 sig_type=std_logic lab=Vip}
C {devices/code.sym} -300 -170 0 0 {name=TT_MODELS
only_toplevel=true
format="tcleval( @value )"
value="
** opencircuitdesign pdks install
.lib $::SKYWATER_MODELS/sky130.lib.spice tt
"
spice_ignore=false}
C {devices/code_shown.sym} -520 -80 0 0 {name=NGSPICE only_toplevel=true 
value="
.param temp=25
.option savecurrents
Vvdd VDD 0 1.8
.param W_1=0.42
.param W_2=0.42
.param L_1=0.5
.param L_2=0.6
.param ID=2.3916u
.control
  save all
  op
  write tb_5t-ota_slew.raw
.endc
"}
C {gnd.sym} -210 140 0 0 {name=l5 lab=GND}
C {lab_pin.sym} 0 80 1 0 {name=p2 sig_type=std_logic lab=Vc}
C {code.sym} 170 50 0 0 {name=SLEW only_toplevel=false
value="
.control
  tran 10n 30u 10u
  save all

  plot v(vip) v(vout)
  
  meas tran v_max FIND v(vout) AT=29u
  meas tran v_min FIND v(vout) AT=11u

  let v10 = v_min + (0.1*(v_max-v_min))
  let v90 = v_max - (0.1*(v_max-v_min))
  meas tran t10 WHEN v(vout)=v10 RISE=1
  meas tran t90 WHEN v(vout)=v90 RISE=1

  let slew_rate = ((v90 - v10) / (t90 - t10)) * 1e-6
  print slew_rate
.endc
"}
C {devices/launcher.sym} -460 -170 0 0 {name=h15
descr="Annotate OP" 
tclcommand="set show_hidden_texts 1; xschem annotate_op"
}
C {capa.sym} 200 -120 0 0 {name=C1
m=1
value=2p
footprint=1206
device="ceramic capacitor"}
C {sky130_fd_pr/pfet_01v8.sym} -70 -100 0 1 {name=M3
W=W_2
L=L_2
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
C {sky130_fd_pr/pfet_01v8.sym} 70 -100 0 0 {name=M4
W=W_2
L=L_2
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
C {gnd.sym} 260 -150 0 0 {name=l3 lab=GND}
C {lab_pin.sym} -90 -50 0 0 {name=p1 sig_type=std_logic lab=Vx}
