import { DotLottieReact } from '@lottiefiles/dotlottie-react';

export function AppLoader() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white">
      <DotLottieReact
        src="https://lottie.host/c4cc4163-1994-4321-b52f-356077798735/CYt2M3yTRw.lottie"
        loop
        autoplay
        style={{ width: 200, height: 200 }}
      />
      <p className="mt-4 text-sm font-medium text-warelyn-muted animate-pulse">Loading Warelyn...</p>
    </div>
  );
}
