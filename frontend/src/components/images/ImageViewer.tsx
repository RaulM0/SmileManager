import { useEffect, useRef } from "react";
import OpenSeadragon from "openseadragon";
type ViewerControl = { element?: HTMLElement; raiseEvent: (name: string, event: { originalEvent: KeyboardEvent }) => void };
type ControlName = "zoomInButton" | "zoomOutButton" | "homeButton" | "fullPageButton" | "rotateLeftButton" | "rotateRightButton";

export default function ImageViewer({ url }: { url: string }) {
  const element = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!url || !element.current) return;
    const viewer = OpenSeadragon({
      element: element.current,
      prefixUrl: `${import.meta.env.BASE_URL}openseadragon/images/`,
      tileSources: { type: "image", url },
      showNavigator: true,
      showRotationControl: true,
      maxZoomLevel: 20,
    });
    const controls = viewer as typeof viewer & Partial<Record<ControlName, ViewerControl>>;
    const labels: Array<[ViewerControl | undefined, string]> = [
      [controls.zoomInButton, "Acercar"],
      [controls.zoomOutButton, "Alejar"],
      [controls.homeButton, "Restablecer vista"],
      [controls.fullPageButton, "Pantalla completa"],
      [controls.rotateLeftButton, "Girar a la izquierda"],
      [controls.rotateRightButton, "Girar a la derecha"],
    ];
    const spaceHandlers: Array<[HTMLElement, (event: KeyboardEvent) => void]> = [];
    labels.forEach(([button, label]) => {
      if (!button?.element) return;
      button.element.setAttribute("role", "button");
      button.element.setAttribute("aria-label", label);
      button.element.tabIndex = 0;
      button.element.title = label;
      const onSpace = (event: KeyboardEvent) => {
        if (event.code !== "Space") return;
        event.preventDefault();
        if (!event.repeat) button.raiseEvent("click", { originalEvent: event });
      };
      button.element.addEventListener("keydown", onSpace);
      spaceHandlers.push([button.element, onSpace]);
    });
    return () => {
      spaceHandlers.forEach(([control, handler]) => control.removeEventListener("keydown", handler));
      viewer.destroy();
    };
  }, [url]);
  return <div ref={element} className="image-viewer" />;
}
