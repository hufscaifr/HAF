import { useEffect, useMemo, useRef, useState } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { COUNTRY_META } from './calendarData';

const WORLD_GEOJSON_URL =
  'https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson';

function EventGlobe({ country = 'GLOBAL', zoomed = false }) {
  const globeRef = useRef(null);
  const wrapRef = useRef(null);
  const [size, setSize] = useState({ width: 360, height: 360 });
  const [countries, setCountries] = useState([]);
  const target = COUNTRY_META[country] || COUNTRY_META.GLOBAL;

  const globeMaterial = useMemo(
    () =>
      new THREE.MeshPhongMaterial({
        color: '#ffffff',
        emissive: '#f6f8fa',
        shininess: 8,
      }),
    []
  );

  const markerData = useMemo(
    () => [
      {
        lat: target.lat,
        lng: target.lon,
        name: target.name,
        country: target.flag,
        color: '#ff6b35',
      },
    ],
    [target]
  );

  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return undefined;

    const updateSize = () => {
      const rect = wrap.getBoundingClientRect();
      const nextSize = Math.max(280, Math.min(rect.width || 360, 520));
      setSize({ width: nextSize, height: nextSize });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(wrap);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let ignore = false;

    fetch(WORLD_GEOJSON_URL)
      .then((response) => response.json())
      .then((geojson) => {
        if (!ignore && Array.isArray(geojson.features)) {
          setCountries(geojson.features);
        }
      })
      .catch(() => {
        if (!ignore) setCountries([]);
      });

    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!globeRef.current) return;

    globeRef.current.pointOfView(
      {
        lat: target.lat,
        lng: target.lon,
        altitude: zoomed ? 1.55 : 2.15,
      },
      900
    );

    const controls = globeRef.current.controls();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.45;
      controls.enableZoom = false;
    }
  }, [target, zoomed]);

  return (
    <div className={`financial-calendar__globe ${zoomed ? 'zoomed' : ''}`}>
      <div className="financial-calendar__globe-canvas" ref={wrapRef}>
        <Globe
          ref={globeRef}
          width={size.width}
          height={size.height}
          backgroundColor="rgba(0,0,0,0)"
          globeMaterial={globeMaterial}
          atmosphereColor="#d7dde3"
          atmosphereAltitude={0.1}
          polygonsData={countries}
          polygonCapColor={() => 'rgba(143, 149, 158, 0.72)'}
          polygonSideColor={() => 'rgba(143, 149, 158, 0.18)'}
          polygonStrokeColor={() => 'rgba(255, 255, 255, 0.86)'}
          polygonAltitude={0.008}
          pointsData={markerData}
          pointLat="lat"
          pointLng="lng"
          pointColor="color"
          pointAltitude={0.08}
          pointRadius={0.46}
          ringsData={markerData}
          ringLat="lat"
          ringLng="lng"
          ringColor={() => '#ff6b35'}
          ringMaxRadius={5}
          ringPropagationSpeed={1.8}
          ringRepeatPeriod={900}
          labelsData={markerData}
          labelLat="lat"
          labelLng="lng"
          labelText={(point) => point.name}
          labelSize={1.2}
          labelDotRadius={0.45}
          labelColor={() => '#ffffff'}
          labelResolution={2}
        />
      </div>
      <div className="financial-calendar__globe-label">
        <span>{target.flag}</span>
        <strong>{target.name}</strong>
      </div>
    </div>
  );
}

export default EventGlobe;
