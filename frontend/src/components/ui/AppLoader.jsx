import { DotLottieReact } from '@lottiefiles/dotlottie-react';

export function AppLoader() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white px-6 text-center">
      <DotLottieReact
        src="https://lottie.host/c4cc4163-1994-4321-b52f-356077798735/CYt2M3yTRw.lottie"
        loop
        autoplay
        style={{ width: 200, height: 200 }}
      />
      <p className="font-display mt-4 text-base font-semibold text-slate-950">Calibrating forklifts, barcode scanners, and coffee levels...</p>
      <p className="font-display mt-1 text-sm text-slate-700">Warelyn is warming up your workspace.</p>
    </div>
  );
}
