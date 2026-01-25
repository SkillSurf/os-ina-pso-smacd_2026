v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -90 30 -90 80 {lab=Vx}
N 90 30 90 80 {lab=Vx}
N -90 80 90 80 {lab=Vx}
N 50 0 90 -0 {lab=Vx}
N 50 0 50 50 {lab=Vx}
N 50 50 90 50 {lab=Vx}
N -90 -0 -50 0 {lab=Vx}
N -50 0 -50 50 {lab=Vx}
N -90 50 -50 50 {lab=Vx}
N 90 -70 90 -30 {lab=Von}
N -90 -70 -90 -30 {lab=Vop}
N -90 -160 -90 -130 {lab=VDD}
N -90 -160 90 -160 {lab=VDD}
N 90 -160 90 -130 {lab=VDD}
N 90 -50 140 -50 {lab=Von}
N -140 -50 -90 -50 {lab=Vop}
N 0 80 0 100 {lab=Vx}
N 0 160 0 180 {lab=GND}
N -0 -180 -0 -160 {lab=VDD}
N -210 20 -210 40 {lab=Vip}
N -210 120 -210 140 {lab=GND}
N -210 0 -210 20 {lab=Vip}
N -210 40 -210 60 {lab=Vip}
N -210 0 -130 -0 {lab=Vip}
N 130 0 210 0 {lab=Vin}
N 210 20 210 40 {lab=Vin}
N 210 120 210 140 {lab=GND}
N 210 0 210 20 {lab=Vin}
N 210 40 210 60 {lab=Vin}
N 30 -50 90 -50 {lab=Von}
N -90 -50 -30 -50 {lab=Vop}
C {sky130_fd_pr/nfet_01v8.sym} -110 0 0 0 {name=M1
W=0.42
L=0.15
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
W=0.42
L=0.15
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
C {res.sym} 90 -100 0 0 {name=R1
value=455.84k
footprint=1206
device=resistor
m=1}
C {res.sym} -90 -100 0 0 {name=R2
value=455.84k
footprint=1206
device=resistor
m=1}
C {isource.sym} 0 130 0 0 {name=I0 value=3.9488u}
C {gnd.sym} 0 180 0 0 {name=l1 lab=GND}
C {vdd.sym} 0 -180 0 0 {name=l2 lab=VDD}
C {lab_pin.sym} -140 -50 0 0 {name=p1 sig_type=std_logic lab=Vop}
C {lab_pin.sym} 210 0 2 0 {name=p3 sig_type=std_logic lab=Vin}
C {lab_pin.sym} 140 -50 0 1 {name=p4 sig_type=std_logic lab=Von}
C {vsource.sym} -210 90 0 0 {name=Vvip savecurrent=false
value="dc 0.9 ac 1 sin(0 50m 1k)"}
C {lab_pin.sym} -210 0 2 1 {name=p5 sig_type=std_logic lab=Vip}
C {devices/code.sym} -420 50 0 0 {name=TT_MODELS
only_toplevel=true
format="tcleval( @value )"
value="
** opencircuitdesign pdks install
.lib $::SKYWATER_MODELS/sky130.lib.spice tt
"
spice_ignore=false}
C {devices/code_shown.sym} -580 -230 0 0 {name=NGSPICE only_toplevel=true 
value="
.param temp=27
.option savecurrents
Vvdd VDD 0 1.8
.control
  save all
  save @m.xm1.msky130_fd_pr__nfet_01v8[gm]
  save @m.xm2.msky130_fd_pr__nfet_01v8[gm]
  op
  write diff-amp.raw
.endc
"}
C {gnd.sym} -210 140 0 0 {name=l5 lab=GND}
C {vsource.sym} 210 90 0 1 {name=Vvin savecurrent=false
value="dc 0.9 ac -1 sin(0 -50m 1k)"}
C {gnd.sym} 210 140 0 0 {name=l6 lab=GND}
C {lab_pin.sym} 0 80 1 0 {name=p2 sig_type=std_logic lab=Vx}
C {code.sym} 290 -230 0 0 {name=GAIN only_toplevel=false
value="
.control
  tran 1u 5m
  save all

  let v_input_diff = v(vip) - v(vin)
  let v_output_diff = v(vop) - v(von)

  plot v_input_diff v_output_diff

  meas tran v_in_pk  PP v_input_diff from=1m to=5m
  meas tran v_out_pk PP v_output_diff from=1m to=5m

  let voltage_gain = v_out_pk / v_in_pk
  print voltage_gain
.endc
"}
C {devices/launcher.sym} -250 -230 0 0 {name=h15
descr="Annotate OP" 
tclcommand="set show_hidden_texts 1; xschem annotate_op"
}
C {code.sym} 290 -70 0 0 {name=SLEW only_toplevel=false
value="
.control
  alter Vvip pulse = [ 850m 950m 0 1n 1n 0.5m 1m 1 ]
  alter Vvin pulse = [ 950m 850m 0 1n 1n 0.5m 1m 1 ]
  tran 10n 520u 480u
  save all

  let v_diff = v(vop) - v(von)
  plot v_diff
  
  meas tran v_max FIND v_diff AT=520u
  meas tran v_min FIND v_diff AT=490u

  let v10 = v_min + 0.1*(v_max-v_min)
  let v90 = v_max - 0.1*(v_max-v_min)
  meas tran t10 WHEN v_diff=v10 RISE=1
  meas tran t90 WHEN v_diff=v90 RISE=1

  let slew_rate = ((v90 - v10) / (t90 - t10)) * 1e-6
  print slew_rate
.endc
"}
C {capa.sym} 0 -50 3 0 {name=C1
m=1
value=2p
footprint=1206
device="ceramic capacitor"}
C {code.sym} 290 90 0 0 {name=GBW only_toplevel=false
value="
.control
  ac dec 100 0.1 1G
  save all

  let diff_gain = (v(vop) - v(von)) / (v(vip) - v(vin))
  let db_diff_gain = db(diff_gain)
  let neg_deg_phase = 180*cph(v(von) - v(vop))/pi

  meas ac gbw_freq WHEN db_diff_gain=0 FALL=1
  let gbw_Mfreq = gbw_freq * 1e-6

  plot db_diff_gain neg_deg_phase
  print gbw_Mfreq
.endc
"}
