from pathlib import Path
import subprocess, textwrap, shutil
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs'; FR=OUT/'video_frames'; FR.mkdir(parents=True,exist_ok=True)
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(font_path,34); small=ImageFont.truetype(font_path,24); title=ImageFont.truetype(font_path,48)
slides=[
('1. Problem','Pickers walk unnecessary distance because slotting no longer matches demand.\nControlled zones make unsafe shortcuts unacceptable.'),
('2. Inputs and cleaning','SKUs + dimensions + temperature/compatibility\nOrder lines + pick frequency\nLocations + capacity + blocked status\nReplenishment events + minutes + worker IDs'),
('3. Two objectives','Travel-first: prioritises walking reduction.\nBalanced: protects replenishment congestion and slot churn.\nBoth use the same feasible candidate set.'),
('4. Safety and uncertainty','Hard: zone, blocked, capacity, weight, worker limit.\nSoft: travel, replenishment effort, congestion, churn.\nLow score margin = low confidence = human review.'),
('5. Experiment','Baseline: most frequent current replenishment location.\nTarget: reduce weighted travel without increasing congestion.\nRun: python src/main.py\nInspect: outputs/evaluation.json'),
('6. Decision workflow','Clean -> validate -> score -> review uncertainty -> authorise -> publish change list -> monitor actual travel, congestion, temperature, and workload.'),
('7. Takeaway','This is a working decision-support prototype, not a GMP/GDP release system.\nPilot with real warehouse data and signed quality approval.')]
for i,(head,body) in enumerate(slides):
    im=Image.new('RGB',(1280,720),(20,29,46)); d=ImageDraw.Draw(im)
    d.rectangle((70,80,1210,640),outline=(72,187,160),width=4)
    d.text((110,120),head,font=title,fill=(255,255,255))
    y=230
    for line in body.split('\n'):
        d.text((120,y),line,font=font,fill=(220,230,240)); y+=70
    d.text((110,650),f'Pharma Dynamic Slotting Optimiser  |  slide {i+1}/{len(slides)}',font=small,fill=(150,170,190))
    im.save(FR/f'frame_{i:02d}.png')
if shutil.which('ffmpeg'):
    subprocess.run(['ffmpeg','-y','-framerate','1/25','-i',str(FR/'frame_%02d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-vf','scale=1280:720',str(OUT/'demo_video.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(OUT/'demo_video.mp4')
else: print('FFmpeg not found; slides are in',FR)
