import { useEffect,useRef } from 'react'
import OpenSeadragon from 'openseadragon'
export default function ImageViewer({url}){const element=useRef(null);useEffect(()=>{if(!url)return;const viewer=OpenSeadragon({element:element.current,prefixUrl:'https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/',tileSources:{type:'image',url},showNavigator:true,showRotationControl:true,maxZoomLevel:20});return()=>viewer.destroy()},[url]);return <div ref={element} className="image-viewer"/>}
