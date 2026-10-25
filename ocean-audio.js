/* Gentle synthesized surf: generated locally, with no external audio requests. */
(() => {
    const button=document.getElementById('ocean-sound-toggle');
    const volume=document.getElementById('ocean-sound-volume');
    const status=document.getElementById('ocean-sound-status');
    let context,output,swell,foam,cycleTimer,playing=false;
    try {volume.value=localStorage.getItem('tide-seek-ocean-volume') || '25';} catch {}
    const update=()=>{
        button.setAttribute('aria-pressed',String(playing));
        button.textContent=playing?'≈ Ocean sounds · On':'≈ Ocean sounds · Off';
    };
    function scheduleWave(){
        const now=context.currentTime;
        const length=11+Math.random()*3;
        swell.gain.cancelScheduledValues(now);
        swell.gain.setValueAtTime(.012,now);
        swell.gain.exponentialRampToValueAtTime(.30,now+length*.30);
        swell.gain.linearRampToValueAtTime(.20,now+length*.40);
        swell.gain.exponentialRampToValueAtTime(.012,now+length);
        foam.frequency.cancelScheduledValues(now);
        foam.frequency.setValueAtTime(450,now);
        foam.frequency.exponentialRampToValueAtTime(1700,now+length*.32);
        foam.frequency.exponentialRampToValueAtTime(450,now+length);
        cycleTimer=setTimeout(scheduleWave,length*1000);
    }
    function createSurf(){
        const AudioEngine=window.AudioContext || window.webkitAudioContext;
        if(!AudioEngine)throw new Error('Audio is unavailable in this browser.');
        context=new AudioEngine();
        output=context.createGain();output.gain.value=0;output.connect(context.destination);
        swell=context.createGain();swell.gain.value=.012;swell.connect(output);
        foam=context.createBiquadFilter();foam.type='lowpass';foam.frequency.value=450;foam.Q.value=.3;foam.connect(swell);
        const highpass=context.createBiquadFilter();highpass.type='highpass';highpass.frequency.value=90;highpass.connect(foam);
        const buffer=context.createBuffer(2,Math.floor(context.sampleRate*7),context.sampleRate);
        for(let channel=0;channel<2;channel++){
            const samples=buffer.getChannelData(channel);
            let smooth=0;
            for(let i=0;i<samples.length;i++){
                const noise=Math.random()*2-1;
                smooth=.94*smooth+.06*noise;
                samples[i]=smooth*2+noise*.25;
            }
        }
        const source=context.createBufferSource();source.buffer=buffer;source.loop=true;source.connect(highpass);source.start();
        scheduleWave();
    }
    button.addEventListener('click',async()=>{
        button.disabled=true;
        try {
            if(!context)createSurf();
            if(playing){
                output.gain.cancelScheduledValues(context.currentTime);
                output.gain.setTargetAtTime(0,context.currentTime,.06);
                playing=false;status.textContent='Ocean sounds off.';
            } else {
                await context.resume();
                if(context.state!=='running')throw new Error('Your browser paused audio. Try the sound button again.');
                output.gain.setTargetAtTime(Number(volume.value)/100,context.currentTime,.15);
                playing=true;status.textContent='Gentle ocean wave sounds playing.';
            }
            update();
        } catch(error){playing=false;update();status.textContent=error.message;}
        finally {button.disabled=false;}
    });
    volume.addEventListener('input',()=>{
        try {localStorage.setItem('tide-seek-ocean-volume',volume.value);} catch {}
        if(output && playing)output.gain.setTargetAtTime(Number(volume.value)/100,context.currentTime,.06);
    });
    window.addEventListener('pagehide',()=>{
        clearTimeout(cycleTimer);
        if(context)context.close().catch(()=>{});
        context=null;playing=false;update();
    });
    update();
})();
