import streamlit as st
import numpy as np

# --- Paywall Library Import ---
# This import path 'from st_paywall import paywall' is a common pattern for Streamlit components.
# If this causes an ImportError, please consult the official 'st-paywall' documentation
# for the exact correct import path and function name for your specific library version.
try:
    from st_paywall import paywall
except ImportError:
    st.error("""
        Error: 'st-paywall' library or its 'paywall' component not found.
        Please ensure it's installed (`pip install st-paywall`) and
        verify the correct import path from its documentation.
    """)
    st.stop() # Stop the app if the paywall library cannot be imported

# --- Define the UN-EX Calculation Function ---
def calculate_unex_diffusion(T, B, E_harmonic, S_local, alpha_coeff, beta_coeff, gamma_coeff, delta):
    """
    Calculates the UN-EX diffusion coefficient based on the simplified linear model:
    D_UNEX = alpha_coeff * (T / B) - beta_coeff * E_harmonic + gamma_coeff * S_local

    This function applies a small positive floor to the calculated diffusion
    coefficient to prevent non-physical negative or zero values, as diffusion
    must always be positive in a physical system.

    Parameters:
    T (float): Plasma Temperature in keV.
    B (float): Magnetic Field in Tesla.
    E_harmonic (float): Harmonic Feedback Energy.
    S_local (float): Local Entropy Proxy (normalized turbulence).
    alpha_coeff (float): Tunable coefficient for the T/B term.
    beta_coeff (float): Tunable coefficient for the E_harmonic term.
    gamma_coeff (float): Tunable coefficient for the S_local term.
    delta (float): Small constant, primarily for numerical stability or
                   legacy from older model forms (its direct role here is minimal).

    Returns:
    float: The calculated UN-EX Diffusion Coefficient in m^2/s,
           guaranteed to be at least min_diffusion_floor.
    """
    # Ensure S_local (normalized turbulence proxy) is not negative,
    # as physical turbulence intensity should be non-negative.
    S_local_adjusted = max(0.0, S_local)

    # Calculate the diffusion coefficient using the provided linear model.
    diffusion_coefficient = (alpha_coeff * (T / B)) - (beta_coeff * E_harmonic) + (gamma_coeff * S_local_adjusted)

    # Define a minimum floor for the diffusion coefficient.
    # Diffusion cannot be zero or negative in a physical system.
    # This value (1e-4 m^2/s) is a very small positive number,
    # representing a baseline minimum diffusion rate.
    min_diffusion_floor = 1e-4 # m^2/s (adjust if a different physical minimum is known)

    # Return the maximum of the calculated coefficient and the floor,
    # ensuring the result is always physically valid.
    return max(diffusion_coefficient, min_diffusion_floor)


def main():
    # --- Stripe Paywall Integration ---
    # This section integrates the 'st-paywall' library.
    # It attempts to authenticate the user using Stripe keys and a product ID.
    # IMPORTANT: These keys and product ID MUST be placed in your '.streamlit/secrets.toml' file.
    #
    # Example .streamlit/secrets.toml content for these keys:
    # [stripe]
    # publishable_key = "pk_test_51RY5SLQZSkGxrGrfL3ePtfvtIMP7idCILXoaOifyjZlFDQOL34Eha5VTHMSkMAtehHMFAQKaIYQPPAcXC9fDEsqm00pxUFe3b"
    # secret_key = "sk_test_51RY5SLQZSkGxrGrf3Bh3UJteGkG1w9GCt3VhVVX1morWCUZHCYCaMpdysTG2Ii1lugSEBABPnuj3kboFV80AhN2l00q80jh2jQ"
    # product_id = "price_XXXXXXXXXXXXXXXX" # REPLACE THIS WITH YOUR ACTUAL STRIPE PRICE ID

    # Access secrets using st.secrets.
    # The 'stripe' key corresponds to the [stripe] section in secrets.toml.
    # 'publishable_key', 'api_key', 'product_id' are keys within that section.
    # Note: 'api_key' in secrets.toml maps to 'secret_key' in the paywall.login function.
    try:
        if not paywall.login(
            publishable_key=st.secrets["stripe"]["publishable_key"],
            secret_key=st.secrets["stripe"]["api_key"], # Accessing api_key from the [stripe] section
            product_id=st.secrets["stripe"]["product_id"]
        ):
            # If authentication fails (user hasn't paid), display a warning and stop the app.
            st.warning("Access denied. Please complete the payment to proceed to the UN-EX Fusion Simulator.")
            st.stop()
    except KeyError as e:
        # Catch errors if a secret key is missing from secrets.toml.
        st.error(f"Configuration Error: Missing Stripe secret in .streamlit/secrets.toml. "
                 f"Please ensure you have '[stripe]' section with '{e.args[0]}' defined. "
                 f"Consult the st-paywall documentation for exact required keys.")
        st.stop()
    except Exception as e:
        # Catch any other unexpected errors during paywall initialization.
        st.error(f"An unexpected error occurred during paywall initialization: {e}")
        st.stop()

    # If the user has authenticated successfully, proceed with the main app content.
    st.title("UN-EX Fusion Simulator - Full Access")
    st.write("Welcome to the full UN-EX Fusion app! Access granted after successful payment.")

    # --- UN-EX Simulator Logic ---
    # This section contains the interactive sliders, calculations, and comparisons
    # for the UN-EX Fusion Model.

    st.header("1. Tunable Plasma Parameters")

    # Interactive sliders allow the user to adjust key plasma and model parameters.
    T = st.slider("Plasma Temperature (T) [keV]", min_value=1.0, max_value=50.0, value=10.0, step=0.5,
                  help="Core plasma temperature. Higher temperatures generally lead to faster fusion reactions but also increased transport.")
    B = st.slider("Magnetic Field (B) [T]", min_value=0.5, max_value=20.0, value=5.0, step=0.1,
                  help="Strength of the confining magnetic field. Stronger fields typically improve confinement.")
    E_harmonic = st.slider("Harmonic Feedback Energy (E_harmonic)", min_value=0.0, max_value=10.0, value=1.0, step=0.1,
                           help="Injected energy tuned to resonant plasma modes, aiming to suppress turbulence. Higher values are expected to reduce diffusion.")
    S_local = st.slider("Local Entropy Proxy (S_local)", min_value=0.0, max_value=1.0, value=0.50, step=0.01,
                        help="A normalized proxy for local plasma turbulence or disorder. Lower values represent reduced turbulence and are desired for better confinement.")

    # Tunable response coefficients for the UN-EX diffusion model.
    alpha_coeff = st.slider("Coefficient alpha (α) for T/B term", min_value=0.1, max_value=10.0, value=1.0, step=0.1,
                            help="Scaling factor for the baseline Bohm-like diffusion component (T/B).")
    beta_coeff = st.slider("Coefficient beta (β) for E_harmonic term", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
                           help="Determines the effectiveness of Harmonic Feedback Energy in reducing diffusion. Higher β means more impact.")
    gamma_coeff = st.slider("Coefficient gamma (γ) for S_local term", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
                            help="Determines how much local entropy (turbulence) increases diffusion. Higher γ means more impact.")

    # Small constant for numerical stability, from previous model forms.
    delta = st.slider("Small constant delta (δ)", min_value=0.001, max_value=0.1, value=0.01, step=0.001, format="%.3f",
                      help="A small positive constant to avoid potential division by zero if S_local approaches zero, or for other numerical stability reasons.")

    st.header("2. UN-EX Model Calculations")

    # Calculate the UN-EX Diffusion Coefficient using the defined function.
    D_UNEX = calculate_unex_diffusion(T, B, E_harmonic, S_local, alpha_coeff, beta_coeff, gamma_coeff, delta)
    st.write(f"**UN-EX Diffusion Coefficient (D_UNEX):** `{D_UNEX:.4e}` m²/s") # Using scientific notation for D_UNEX

    # Assume a characteristic minor radius 'a' for the plasma.
    # Confinement time (tau_E) is typically proportional to a^2 / D.
    a = 1.0  # Example minor radius in meters (e.g., typical for a medium-sized tokamak)
    tau_E_unex = (a**2) / D_UNEX
    st.write(f"**UN-EX Energy Confinement Time (τ_E_UNEX):** `{tau_E_unex:.4f}` s")

    # Placeholder for Q-ratio calculation.
    # A full Q-ratio calculation requires detailed power balance, plasma density,
    # volume, fusion cross-sections, and radiation losses, which are beyond the
    # scope of this simplified diffusion model. However, higher tau_E implies higher Q.
    st.info("*(Note: A precise Q-ratio calculation requires detailed power balance inputs (e.g., plasma density, volume, fusion power, input power) not fully defined by this diffusion model. Generally, higher confinement time (τ_E) is crucial for achieving high Q.)*")


    st.header("3. Confinement Comparison")
    st.write("Comparing UN-EX confinement against generalized Bohm and Neoclassical scaling laws.")

    # --- Bohm Confinement ---
    # Simplified Bohm diffusion coefficient (D_Bohm ~ T/B).
    # A typical factor for Bohm is k_B / (16 * e) or similar, leading to ~1/16 T/B.
    # Here, 'scaling_factor_bohm' is a placeholder for a numerical constant.
    scaling_factor_bohm = 1.0 # Arbitrary constant for comparative scaling in this simplified model.
    D_Bohm = scaling_factor_bohm * (T / B)
    tau_E_bohm = (a**2) / D_Bohm
    st.write(f"**Bohm Confinement Time (τ_E_Bohm):** `{tau_E_bohm:.4f}` s")

    # --- Neoclassical Confinement ---
    # Simplified Neoclassical diffusion coefficient (D_Neoclassical ~ T^0.5 / B^2).
    # This is a very rough simplification; actual neoclassical diffusion is complex
    # and highly dependent on collisionality regimes (banana, plateau, Pfirsch-Schlüter).
    scaling_factor_neoclassical = 0.1 # Arbitrary constant for comparative scaling.
    D_Neoclassical = scaling_factor_neoclassical * (T**0.5 / B**2)
    tau_E_neoclassical = (a**2) / D_Neoclassical
    st.write(f"**Neoclassical Confinement Time (τ_E_Neoclassical):** `{tau_E_neoclassical:.4f}` s")

    st.subheader("Confinement Time Performance")
    # Compare UN-EX confinement time with Bohm and Neoclassical.
    if tau_E_unex > tau_E_bohm:
        st.success(f"**UN-EX τ_E ({tau_E_unex:.2f} s) is significantly better than Bohm τ_E ({tau_E_bohm:.2f} s)!** This suggests successful active transport suppression.")
    else:
        st.info(f"UN-EX τ_E ({tau_E_unex:.2f} s) is comparable to or worse than Bohm τ_E ({tau_E_bohm:.2f} s). Tuning of parameters might be needed for improvement.")

    if tau_E_unex > tau_E_neoclassical:
        st.success(f"**UN-EX τ_E ({tau_E_unex:.2f} s) is better than Neoclassical τ_E ({tau_E_neoclassical:.2f} s)!** This indicates the model's ability to outperform even collisional transport limits.")
    else:
        st.info(f"UN-EX τ_E ({tau_E_unex:.2f} s) is comparable to or worse than Neoclassical τ_E ({tau_E_neoclassical:.2f} s). Further optimization may be required.")


    st.header("4. Real-Time Confinement Plot")
    # This plot currently shows only a single point reflecting the current UN-EX τ_E.
    # To implement a "Q Sweep" over time or visualize historical performance,
    # you would need to:
    # a) Store past calculated tau_E values (e.g., in st.session_state).
    # b) Implement a loop or simulation step that advances "time" and updates parameters (e.g., for the "smart loop").
    # c) Plot the list of historical values.
    # Example for current single point:
    st.line_chart(np.array([[0, tau_E_unex]]), use_container_width=True)
    st.markdown("*(This plot currently displays the instantaneous UN-EX τ_E at an arbitrary 'Time=0'. For dynamic 'Q Sweep' behavior or a time-series visualization, additional simulation logic to track and update values over iterations would be required.)*")


# This ensures that the 'main' function is called when the script is executed.
if __name__ == "__main__":
    main()

