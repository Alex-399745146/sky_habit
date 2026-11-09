(() => {
  const canvas = document.getElementById("matrix-rain");

  if (!canvas || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  const context = canvas.getContext("2d");

  if (!context) {
    return;
  }

  const glyphs = "01";
  const fontSize = 14;
  const fps = 20;
  const fadeColor = "rgba(2, 5, 3, 0.14)";

  let width = 0;
  let height = 0;
  let columns = [];
  let frame = 0;
  let lastFrame = 0;

  const randomSpeed = () => fontSize * (0.5 + Math.random());

  function resize() {
    const rect = canvas.getBoundingClientRect();

    if (!rect.width || !rect.height) {
      return;
    }

    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);

    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    context.font = `${fontSize}px "Share Tech Mono", "Courier New", monospace`;
    context.textBaseline = "top";

    width = rect.width;
    height = rect.height;

    columns = Array.from({ length: Math.ceil(width / fontSize) }, () => ({
      y: Math.random() * -height,
      speed: randomSpeed(),
    }));

    context.fillStyle = "rgba(2, 5, 3, 1)";
    context.fillRect(0, 0, width, height);
  }

  function draw() {
    context.fillStyle = fadeColor;
    context.fillRect(0, 0, width, height);

    for (let index = 0; index < columns.length; index += 1) {
      const column = columns[index];
      const x = index * fontSize;

      if (column.y > 0) {
        const char = glyphs[Math.floor(Math.random() * glyphs.length)];
        context.fillStyle = Math.random() > 0.965 ? "#eafff1" : "rgba(0, 255, 102, 0.78)";
        context.fillText(char, x, column.y);
      }

      column.y += column.speed;

      if (column.y > height + fontSize * 2) {
        column.y = -Math.random() * height * 0.5;
        column.speed = randomSpeed();
      }
    }
  }

  function loop(timestamp) {
    frame = window.requestAnimationFrame(loop);

    if (timestamp - lastFrame < 1000 / fps) {
      return;
    }

    lastFrame = timestamp;
    draw();
  }

  function start() {
    if (!frame) {
      frame = window.requestAnimationFrame(loop);
    }
  }

  function stop() {
    if (frame) {
      window.cancelAnimationFrame(frame);
      frame = 0;
    }
  }

  resize();

  if (width > 0 && height > 0) {
    start();
  }

  let resizeTimer = 0;
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => {
      stop();
      resize();
      start();
    }, 200);
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stop();
    } else {
      start();
    }
  });

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          start();
        } else {
          stop();
        }
      });
    });

    observer.observe(canvas);
  }
})();
