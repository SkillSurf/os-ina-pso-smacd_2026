v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
N -80 10 40 10 {
lab=VB1}
N -80 30 40 30 {
lab=VB2}
N -80 50 40 50 {
lab=VB3}
N -80 70 40 70 {
lab=VB4}
N -230 180 160 180 {
lab=AVSS}
N 160 100 160 180 {
lab=AVSS}
N 120 100 120 140 {
lab=VCM}
N 220 -20 270 -20 {
lab=VO1}
N 220 -60 270 -60 {
lab=VO2}
N -230 -130 160 -130 {
lab=AVDD}
N -230 -130 -230 -40 {
lab=AVDD}
N -440 30 -380 30 {
lab=IREF}
N -10 -30 40 -30 {
lab=VI_2A}
N -10 -70 40 -70 {
lab=VI_1A}
N -10 -10 40 -10 {
lab=VI_2B}
N -10 -50 40 -50 {
lab=VI_1B}
N -290 -130 -230 -130 {
lab=AVDD}
N 50 -270 50 -250 {
lab=AVSS}
N 340 -270 340 -250 {
lab=AVSS}
N -260 -270 -260 -250 {
lab=AVSS}
N -550 -270 -550 -250 {
lab=AVSS}
N -470 90 -470 110 {
lab=AVSS}
N 440 100 440 120 {
lab=AVSS}
N 440 -70 440 -50 {
lab=AVSS}
N -530 30 -440 30 {
lab=IREF}
N 440 20 440 40 {
lab=VO1}
N 440 -150 440 -130 {
lab=VO2}
N 340 -350 340 -330 {
lab=VI_2B}
N 50 -350 50 -330 {
lab=VI_2A}
N -260 -350 -260 -330 {
lab=VI_1B}
N -550 -350 -550 -330 {
lab=VI_1A}
N 120 330 120 350 {
lab=AVSS}
N 120 250 120 270 {
lab=VO1}
C {devices/iopin.sym} -530 30 0 1 {name=p1 lab=IREF}
C {INA_layout_v2/dda.sym} 130 -40 0 0 {name=x1}
C {devices/iopin.sym} -10 -70 0 1 {name=p2 lab=VI_1A}
C {devices/iopin.sym} -10 -50 0 1 {name=p3 lab=VI_1B}
C {devices/iopin.sym} -10 -30 0 1 {name=p4 lab=VI_2A}
C {devices/iopin.sym} -10 -10 0 1 {name=p5 lab=VI_2B}
C {devices/iopin.sym} 270 -60 0 0 {name=p6 lab=VO2}
C {devices/iopin.sym} 270 -20 0 0 {name=p7 lab=VO1}
C {devices/iopin.sym} 120 140 0 1 {name=p8 lab=VCM}
C {devices/iopin.sym} -290 -130 0 1 {name=p9 lab=AVDD}
C {devices/iopin.sym} 160 140 0 0 {name=p10 lab=AVSS}
C {devices/lab_wire.sym} 20 10 0 0 {name=p11 sig_type=std_logic lab=VB1}
C {devices/lab_wire.sym} 20 30 0 0 {name=p12 sig_type=std_logic lab=VB2}
C {devices/lab_wire.sym} 20 50 0 0 {name=p13 sig_type=std_logic lab=VB3}
C {devices/lab_wire.sym} 20 70 0 0 {name=p14 sig_type=std_logic lab=VB4}
C {INA_layout_v2/bias/bias.sym} -230 70 0 0 {name=x2}
C {sky130_fd_pr/diode.sym} 50 -300 0 0 {name=D3
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} 50 -250 2 0 {name=p19 sig_type=std_logic lab=AVSS}
C {sky130_fd_pr/diode.sym} 340 -300 0 0 {name=D4
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} 340 -250 2 0 {name=p20 sig_type=std_logic lab=AVSS}
C {sky130_fd_pr/diode.sym} -260 -300 0 0 {name=D5
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} -260 -250 2 0 {name=p21 sig_type=std_logic lab=AVSS}
C {sky130_fd_pr/diode.sym} -550 -300 0 0 {name=D6
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} -550 -250 2 0 {name=p22 sig_type=std_logic lab=AVSS}
C {sky130_fd_pr/diode.sym} -470 60 0 0 {name=D7
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} -470 110 2 0 {name=p23 sig_type=std_logic lab=AVSS}
C {sky130_fd_pr/diode.sym} 440 70 0 0 {name=D2
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} 440 120 2 0 {name=p24 sig_type=std_logic lab=AVSS}
C {sky130_fd_pr/diode.sym} 440 -100 0 0 {name=D1
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} 440 -50 2 0 {name=p25 sig_type=std_logic lab=AVSS}
C {devices/lab_wire.sym} -260 -350 0 0 {name=p15 sig_type=std_logic lab=VI_1B}
C {devices/lab_wire.sym} -550 -350 0 0 {name=p16 sig_type=std_logic lab=VI_1A}
C {devices/lab_wire.sym} 50 -350 0 0 {name=p17 sig_type=std_logic lab=VI_2A}
C {devices/lab_wire.sym} 340 -350 0 0 {name=p18 sig_type=std_logic lab=VI_2B}
C {devices/lab_wire.sym} 440 -150 0 0 {name=p26 sig_type=std_logic lab=VO2}
C {devices/lab_wire.sym} 440 20 0 0 {name=p27 sig_type=std_logic lab=VO1}
C {sky130_fd_pr/diode.sym} 120 300 0 0 {name=D8
model=diode_pw2nd_05v5
area=0.2025e12
pj=1.8e6
}
C {devices/lab_wire.sym} 120 350 2 0 {name=p28 sig_type=std_logic lab=AVSS}
C {devices/lab_wire.sym} 120 250 0 0 {name=p29 sig_type=std_logic lab=VCM}
