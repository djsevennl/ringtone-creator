// Isolated Cloudflare Worker connectivity test for Ringtone Creator.
// Deploy only to a NEW Worker; never overwrite the existing Circle of Jay Worker.
// No audio is stored or proxied. Do not treat successful metadata as working conversion.
const PROVIDERS = [
  'https://pipedapi.kavin.rocks',
  'https://pipedapi.leptons.xyz',
  'https://pipedapi.nosebs.ru'
];
const json=(data,status=200)=>new Response(JSON.stringify(data),{
  status,headers:{'content-type':'application/json; charset=utf-8','access-control-allow-origin':'*','cache-control':'no-store'}
});
export default {
  async fetch(request){
    if(request.method==='OPTIONS')return new Response(null,{status:204,headers:{
      'access-control-allow-origin':'*','access-control-allow-methods':'GET, OPTIONS','access-control-allow-headers':'content-type'
    }});
    if(request.method!=='GET')return json({error:'Method not allowed'},405);
    const url=new URL(request.url);
    if(url.pathname==='/health')return json({ok:true,service:'ringtone-audio-test',mode:'metadata-only'});
    if(url.pathname!=='/probe')return json({error:'Use /health or /probe?id=VIDEO_ID'},404);
    const id=url.searchParams.get('id')||'';
    if(!/^[A-Za-z0-9_-]{11}$/.test(id))return json({error:'Invalid video ID'},400);
    const results=[];
    for(const provider of PROVIDERS){
      const controller=new AbortController();
      const timeout=setTimeout(()=>controller.abort(),6500);
      try{
        const response=await fetch(provider+'/streams/'+encodeURIComponent(id),{
          signal:controller.signal,headers:{accept:'application/json'}
        });
        if(!response.ok)throw new Error('HTTP '+response.status);
        const data=await response.json();
        const audio=Array.isArray(data.audioStreams)?data.audioStreams:[];
        results.push({provider,reachable:true,audioStreams:audio.length});
        if(audio.length)return json({ok:true,provider,audioStreams:audio.length,results,note:'Metadata only; audio download not verified'});
      }catch(error){results.push({provider,reachable:false,error:String(error.message||error).slice(0,160)})}
      finally{clearTimeout(timeout)}
    }
    return json({ok:false,results,note:'No audio conversion available'},502);
  }
};
