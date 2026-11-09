document.addEventListener("DOMContentLoaded", () => {
  const pleasant = document.getElementById("id_is_pleasant");
  const linked = document.getElementById("id_linked_habit");
  const reward = document.getElementById("id_reward");

  if (!pleasant || !linked || !reward) {
    return;
  }

  const wrapper = (element) => element.closest(".mb-3");

  const sync = () => {
    const disabled = pleasant.checked;
    linked.disabled = disabled;
    reward.disabled = disabled;

    if (disabled) {
      linked.value = "";
      reward.value = "";
    }

    [linked, reward].forEach((element) => {
      const box = wrapper(element);
      if (box) {
        box.classList.toggle("opacity-50", disabled);
      }
    });
  };

  pleasant.addEventListener("change", sync);
  sync();
});
