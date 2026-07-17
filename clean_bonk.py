import re
import os
import shutil
from urllib.parse import unquote

# Change directory to the script's directory to ensure relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 1. Rename BONK COIN_files to assets if it exists
if os.path.exists("BONK COIN_files") and not os.path.exists("assets"):
    os.rename("BONK COIN_files", "assets")
    print("Renamed folder to assets")
elif os.path.exists("BONK COIN_files") and os.path.exists("assets"):
    shutil.rmtree("assets")
    os.rename("BONK COIN_files", "assets")
    print("Overwrote assets folder with BONK COIN_files")
else:
    print("assets folder already exists and BONK COIN_files does not.")

# 2. Read BONK COIN.html
with open("BONK COIN.html", "r", encoding="utf-8") as f:
    content = f.read()

# 3. Clean up Next.js hydration scripts
content = re.sub(r'<link rel="preload" as="script"[^>]+>', '', content)
content = re.sub(r'<script src="https://www\.bonkcoin\.com/_next/static/chunks/[^>]+></script>', '', content)
content = re.sub(r'<script src="[^"]*recaptcha[^"]*"[^>]*></script>', '', content)
content = re.sub(r'<script>\(self\.__next_f[^<]+</script>', '', content)
content = re.sub(r'<script>self\.__next_f[^<]+</script>', '', content)
content = re.sub(r'<script src="https://www\.bonkcoin\.com/_next/static/chunks/f980f3bed661f14d\.js[^>]+></script>', '', content)

# 4. Point main stylesheet to local assets
content = re.sub(
    r'href="https://www\.bonkcoin\.com/_next/static/chunks/af6eef9841044a55\.css[^"]*"',
    'href="assets/af6eef9841044a55.css"',
    content
)

# 5. Fix image URLs
# We want to replace Next.js image endpoint URLs and direct media URLs to the simple local asset names
def replace_img_url(match):
    url_param = match.group(1)
    decoded_url = unquote(url_param)
    filename_match = re.search(r'([a-zA-Z0-9_-]+)\.[a-f0-9]+\.(png|jpg|jpeg|gif|svg|webp)', decoded_url)
    if filename_match:
        base_name = filename_match.group(1)
        ext = filename_match.group(2)
        return f'src="assets/{base_name}.{ext}"'
    return match.group(0)

# Replace Next.js image optimizer URL pattern
content = re.sub(r'src="https://www\.bonkcoin\.com/_next/image\?url=([^"&]+)(?:&amp;[^"]*|)"', replace_img_url, content)
content = re.sub(r'src="https://www\.bonkcoin\.com/_next/image\?url=([^"&]+)"', replace_img_url, content)

# Also handle static media URLs
def replace_static_media(match):
    base_name = match.group(1)
    ext = match.group(2)
    return f'src="assets/{base_name}.{ext}"'

content = re.sub(r'src="https://www\.bonkcoin\.com/_next/static/media/([a-zA-Z0-9_-]+)\.[a-f0-9]+\.(png|jpg|jpeg|gif|svg|webp)"', replace_static_media, content)

# Remove srcSet and sizes properties so browser displays the high-quality local assets
content = re.sub(r'\s*srcSet="[^"]+"', '', content)
content = re.sub(r'\s*sizes="[^"]+"', '', content)

# 6. Fix general opacities (opacity:0) on load elements
# Replace style="opacity:0;transform:translateY(10px)" or style="opacity:0"
content = re.sub(r'style="opacity:0;transform:translateY\(10px\)"', '', content)
content = re.sub(r'style="opacity:0;transform:translateY\(20px\)"', '', content)
content = re.sub(r'style="opacity:0"', '', content)

# 7. Setup responsive classes for the two hero videos:
# Video 1: Mobile video wrapper (object-[75%] class)
# Video 2: Desktop video wrapper (object-[50%] class)
# We find the video tags and their parent divs. Since we removed style="opacity:0", parent looks like <div class="absolute inset-0 -z-10">
video_pattern = r'(<div class="absolute inset-0 -z-10"\s*>)(<video[^>]*class="[^"]*object-\[75%\][^"]*"[^>]*>)'
content = re.sub(video_pattern, r'<div class="absolute inset-0 -z-10 block lg:hidden">\2', content)

video_pattern2 = r'(<div class="absolute inset-0 -z-10"\s*>)(<video[^>]*class="[^"]*object-\[50%\][^"]*"[^>]*>)'
content = re.sub(video_pattern2, r'<div class="absolute inset-0 -z-10 hidden lg:block">\2', content)

# 8. Inject Google Fonts and styles in head, and write custom JavaScript for interactivity
head_injection = """
    <!-- Google Fonts Integration -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        :root {
            --font-poppins: 'Poppins', sans-serif !important;
            --font-space-mono: 'Space Mono', monospace !important;
        }
        .font-poppins {
            font-family: 'Poppins', sans-serif !important;
        }
        .font-space-mono {
            font-family: 'Space Mono', monospace !important;
        }
        /* Custom Marquee Animation fallback in case Tailwind's doesn't start */
        @keyframes marquee {
            0% { transform: translateX(0%); }
            100% { transform: translateX(-50%); }
        }
        .animate-marquee-custom {
            display: flex;
            width: max-content;
            animation: marquee 30s linear infinite;
        }
    </style>
</head>
"""
content = content.replace("</head>", head_injection)

# Now, write the custom JavaScript for interactivity at the bottom of the body (before </body>)
body_injection = """
    <!-- Custom Interactive Scripts -->
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            // --- A. POSSIBILITIES CARDS FLIP/REVEAL ---
            const cards = document.querySelectorAll(".relative.w-full.sm\\\\:max-w-80");
            cards.forEach(card => {
                const frontCard = card.querySelector("div:first-child");
                const backCard = card.querySelector("div:nth-child(2)");
                const revealBtn = frontCard ? frontCard.querySelector("button") : null;
                const closeBtn = backCard ? backCard.querySelector("button") : null;

                if (frontCard && backCard) {
                    // Click on the front card button to reveal description
                    if (revealBtn) {
                        revealBtn.addEventListener("click", (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            backCard.classList.remove("opacity-0", "pointer-events-none");
                            backCard.classList.add("opacity-100", "pointer-events-auto");
                        });
                    }
                    // Click on back card close button to hide description
                    if (closeBtn) {
                        closeBtn.addEventListener("click", (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            backCard.classList.remove("opacity-100", "pointer-events-auto");
                            backCard.classList.add("opacity-0", "pointer-events-none");
                        });
                    }
                }
            });

            // --- B. ECOSYSTEM GATEWAY TABS ---
            const gatewayButtons = document.querySelectorAll("section#gateway button");
            const gatewayDescriptions = document.querySelectorAll("section#gateway .mx-auto.max-w-80.flex-col");
            
            if (gatewayButtons.length > 0 && gatewayDescriptions.length > 0) {
                // Show first description initially
                gatewayDescriptions.forEach((d, i) => {
                    if (i === 0) {
                        d.classList.remove("opacity-0", "hidden");
                        d.classList.add("opacity-100", "flex");
                        gatewayButtons[0].classList.add("bg-white/20");
                    } else {
                        d.classList.add("opacity-0", "hidden");
                    }
                });
                
                gatewayButtons.forEach((btn, index) => {
                    if (index < gatewayDescriptions.length) {
                        btn.addEventListener("click", () => {
                            // Deactivate all
                            gatewayButtons.forEach(b => b.classList.remove("bg-white/20"));
                            gatewayDescriptions.forEach(d => {
                                d.classList.remove("opacity-100", "flex");
                                d.classList.add("opacity-0", "hidden");
                            });
                            // Activate clicked
                            btn.classList.add("bg-white/20");
                            gatewayDescriptions[index].classList.remove("opacity-0", "hidden");
                            gatewayDescriptions[index].classList.add("opacity-100", "flex");
                        });
                    }
                });
            }

            // --- C. MOBILE MENU ---
            const menuBtn = document.querySelector("header button.min-\\\\[1080px\\\\\\\\]\\\\:hidden");
            const navMenu = document.querySelector("header nav");
            if (menuBtn && navMenu) {
                menuBtn.addEventListener("click", () => {
                    navMenu.classList.toggle("hidden");
                    navMenu.classList.toggle("flex");
                    navMenu.classList.toggle("flex-col");
                    navMenu.classList.toggle("absolute");
                    navMenu.classList.toggle("top-16");
                    navMenu.classList.toggle("left-0");
                    navMenu.classList.toggle("w-full");
                    navMenu.classList.toggle("bg-background");
                    navMenu.classList.toggle("p-6");
                    navMenu.classList.toggle("border-b");
                });
            }

            // --- D. LOGO MARQUEE FALLBACK ---
            const marqueeContainer = document.querySelector(".relative.flex.h-20.w-full.flex-col.items-center.justify-center.overflow-hidden");
            if (marqueeContainer) {
                const marqueeInner = marqueeContainer.querySelector(".group.flex");
                if (marqueeInner) {
                    marqueeInner.className = "group flex overflow-hidden p-2 flex-row w-full";
                    const marqueeList = marqueeInner.querySelector("div");
                    if (marqueeList) {
                        const clone = marqueeList.cloneNode(true);
                        marqueeInner.appendChild(clone);
                        marqueeList.className = "animate-marquee-custom flex shrink-0 justify-around gap-12 sm:gap-24 flex-row";
                        clone.className = "animate-marquee-custom flex shrink-0 justify-around gap-12 sm:gap-24 flex-row";
                    }
                }
            }
            
            // --- E. CAROUSELS / SLIDERS ---
            const carousels = document.querySelectorAll('[data-slot="carousel"]');
            carousels.forEach(carousel => {
                const content = carousel.querySelector('[data-slot="carousel-content"]');
                const items = carousel.querySelectorAll('[data-slot="carousel-item"]');
                if (content && items.length > 1) {
                    carousel.style.overflowX = "auto";
                    carousel.style.scrollbarWidth = "none";
                    carousel.style.msOverflowStyle = "none";
                    carousel.addEventListener("wheel", (evt) => {
                        evt.preventDefault();
                        carousel.scrollLeft += evt.deltaY;
                    }, { passive: false });
                }
            });
        });
    </script>
"""
content = content.replace("</body>", body_injection)

# 9. Write out the cleaned HTML to index.html
with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully wrote index.html!")
