def get_estimate_heating_losses(outdoor_temp, in_t=22.0, ref_out=-15, ref_in=20, ref_loss=8.5):
    diff_ref = ref_in - ref_out
    diff_current = in_t - outdoor_temp
    loss = (ref_loss / diff_ref) * diff_current
    return max(loss, 0)