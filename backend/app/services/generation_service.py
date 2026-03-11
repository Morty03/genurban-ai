# backend/app/services/generation_service.py
import os
import io
import numpy as np
from typing import Optional, Tuple, List, Dict
from PIL import Image
import torch
import torch.nn as nn

# Where we expect the saved generator weights (update if you store elsewhere)
CANDIDATE_MODEL_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "ultra_fast_generator.pth")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml_engine", "models", "ultra_fast_generator.pth")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "urban_generator.pth")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml_engine", "models", "urban_generator.pth")),
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class UltraFastGenerator(nn.Module):
    def __init__(self, latent_dim: int = 64, output_channels: int = 5):
        super(UltraFastGenerator, self).__init__()
        self.main = nn.Sequential(
            nn.ConvTranspose2d(latent_dim, 128, 4, 1, 0),  # 4x4
            nn.ReLU(True),
            nn.ConvTranspose2d(128, 64, 4, 2, 1),          # 8x8
            nn.ReLU(True),
            nn.ConvTranspose2d(64, 32, 4, 2, 1),           # 16x16
            nn.ReLU(True),
            nn.ConvTranspose2d(32, output_channels, 4, 2, 1), # 32x32
            nn.Tanh()
        )

    def forward(self, x):
        return self.main(x)


class GenerationService:
    def __init__(self, latent_dim: int = 64, output_channels: int = 5):
        self.latent_dim = latent_dim
        self.output_channels = output_channels
        self.model: Optional[UltraFastGenerator] = None
        self.model_path: Optional[str] = None
        # create model instance (weights will be loaded with load_generator)
        self.model = UltraFastGenerator(self.latent_dim, self.output_channels).to(device)

    def find_model_file(self) -> Optional[str]:
        for p in CANDIDATE_MODEL_PATHS:
            if os.path.exists(p):
                return p
        return None

    def load_generator(self, model_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Attempt to load weights. If not found or load fails, the untrained model instance remains.
        Returns (loaded_flag, used_path_or_none)
        """
        p = model_path or self.find_model_file()
        if p is None:
            self.model_path = None
            return False, None

        try:
            state = torch.load(p, map_location=device)
            # Try direct state_dict, allowing for full module or nested dicts
            if isinstance(state, dict) and any(k.startswith('main') or k.startswith('0') for k in state.keys()):
                # probably state_dict
                self.model.load_state_dict(state)
            else:
                # possibly a state_dict under 'state_dict' or full module; attempt safe load
                try:
                    self.model.load_state_dict(state)
                except Exception:
                    # try to extract 'state_dict' key
                    st = state.get('state_dict') if isinstance(state, dict) else None
                    if st:
                        self.model.load_state_dict(st)
                    else:
                        # last resort: try loading directly (may error)
                        self.model.load_state_dict(state)
            self.model_path = p
            self.model.to(device)
            self.model.eval()
            return True, p
        except Exception as e:
            # keep the untrained model but return failure
            self.model_path = None
            print(f"[generation_service] Failed to load model from {p}: {e}")
            return False, p

    def _sample_noise(self, n: int) -> torch.Tensor:
        return torch.randn(n, self.latent_dim, 1, 1, device=device)

    def generate_from_noise(self, n_samples: int = 1, climate_factors: Optional[Dict] = None) -> np.ndarray:
        """
        Generate samples from random noise.
        climate_factors: optional dict used to alter noise as in your notebook:
            expected keys: 'precipitation', 'temperature', 'urban_heat' — optional
        Returns numpy array shape (n_samples, C, H, W) with values in [-1,1] (because generator uses Tanh)
        """
        if self.model is None:
            # instantiate if somehow missing
            self.model = UltraFastGenerator(self.latent_dim, self.output_channels).to(device)

        self.model.eval()
        noise = self._sample_noise(n_samples)

        # Apply simple climate influence mapping if provided (keeps behavior similar to notebook)
        if climate_factors:
            # Map keys (flexible)
            temp = float(climate_factors.get('temperature', climate_factors.get('avg_temperature', 1.0)))
            precip = float(climate_factors.get('precipitation', climate_factors.get('total_precipitation', 1.0)))
            uhi = float(climate_factors.get('urban_heat', climate_factors.get('urban_heat_island_effect', 1.0)))
            # Normalize to 0..2-ish scale safely
            # Using same multipliers as your notebook: (1 + factor*0.2) etc. — simple approach
            # Note: user notebooks applied different multipliers per scenario; here we apply a gentle mod.
            noise = noise * (1.0 + (precip / (precip + 1.0)) * 0.2 + (temp / (temp + 1.0)) * 0.1 - (uhi / (uhi + 1.0)) * 0.05)

        with torch.no_grad():
            out = self.model(noise)
            arr = out.cpu().numpy()
        return arr  # values in [-1,1]

    def denormalize_to_uint8(self, arr: np.ndarray) -> np.ndarray:
        """
        Convert [-1,1] float array to uint8 0-255. Input shape (N,C,H,W) or (C,H,W).
        We'll clip and rescale per-channel.
        """
        a = arr.copy()
        # scale from [-1,1] -> [0,255]
        a = (a + 1.0) / 2.0
        a = np.clip(a * 255.0, 0, 255).astype(np.uint8)
        return a

    def generate_png_bytes(self, n_samples: int = 1, climate_factors: Optional[Dict] = None, channel_for_display: int = 0, max_size: int = 512) -> List[bytes]:
        """
        Generate samples and return a list of PNG byte blobs for each sample.
        channel_for_display picks which channel to visualize (0-indexed). For multi-channel output, we render the chosen channel as grayscale.
        """
        arr = self.generate_from_noise(n_samples=n_samples, climate_factors=climate_factors)
        # arr shape: (N,C,H,W)
        imgs = []
        for i in range(arr.shape[0]):
            sample = arr[i]  # (C,H,W)
            # if output has >=3 channels, try to use first 3 as RGB
            if sample.shape[0] >= 3:
                rgb = np.stack([
                    sample[0],
                    sample[1],
                    sample[2]
                ], axis=-1)  # H,W,3
                uint8 = self.denormalize_to_uint8(np.transpose(rgb, (2,0,1))) if False else None
                # easier: compute per-band scaling
                rgb_u8 = np.zeros_like(rgb)
                for ch in range(3):
                    band = rgb[:,:,ch]
                    lo, hi = np.percentile(band, (2,98))
                    if hi - lo <= 0:
                        norm = np.clip(band, -1, 1)
                    else:
                        norm = (band - lo) / (hi - lo) * 2 - 1  # keep in -1..1
                    rgb_u8[:,:,ch] = np.clip((norm + 1)/2*255, 0, 255)
                img_arr = rgb_u8.astype(np.uint8)
                im = Image.fromarray(img_arr)
            else:
                # single channel display
                ch = min(channel_for_display, sample.shape[0]-1)
                band = sample[ch]
                # scale percentiles to 0..255
                lo, hi = np.percentile(band, (2,98))
                if hi - lo <= 0:
                    scaled = np.clip(band, -1, 1)
                else:
                    scaled = (band - lo) / (hi - lo) * 2 - 1
                img_arr = np.clip((scaled + 1)/2*255, 0, 255).astype(np.uint8)
                im = Image.fromarray(img_arr, mode="L").convert("RGB")

            # resize for easier download/view
            im.thumbnail((max_size, max_size))
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            imgs.append(buf.getvalue())
        return imgs

    def generate_and_save_png(self, out_dir: str, prefix: str = "gen", n_samples: int = 1, climate_factors: Optional[Dict] = None) -> List[str]:
        """
        Generate PNG(s) and save them under out_dir. Returns list of file paths.
        """
        os.makedirs(out_dir, exist_ok=True)
        pngs = self.generate_png_bytes(n_samples=n_samples, climate_factors=climate_factors)
        paths = []
        for idx, b in enumerate(pngs):
            fname = f"{prefix}_{idx}.png" if n_samples > 1 else f"{prefix}.png"
            fp = os.path.join(out_dir, fname)
            with open(fp, "wb") as f:
                f.write(b)
            paths.append(fp)
        return paths

    def generate_and_store(self, storage_service, name: str, year: int, scenario_tag: str = "generated", n_samples: int = 1, climate_factors: Optional[Dict] = None) -> List[Dict]:
        """
        Generate images and store them using the provided StorageService.
        Returns list of metadata dicts (id, thumb_url, stored_path).
        NOTE: This function stores PNG bytes as tif extension for compatibility with storage_service.
        If you want GeoTIFF georeference, you'll need more code to attach bounds/transform from inputs.
        """
        results = []
        png_bytes_list = self.generate_png_bytes(n_samples=n_samples, climate_factors=climate_factors)
        for i, b in enumerate(png_bytes_list):
            # store as a .tif filename so frontend treats it as raster; thumbnail will be stored separately by existing flow
            # but storage_service expects raster bytes; we pass PNG bytes anyway (works for demo)
            key = storage_service.store_scenario(f"{name}_{i}", year, scenario_tag, b)
            # After store, storage/list will be able to list this id
            results.append({"id": key})
        return results
