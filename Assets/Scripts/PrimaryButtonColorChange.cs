using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Task 3 — Pressing the primary button (X on left / A on right controller)
/// toggles this object's material colour between two configurable colours.
/// Assign the Left/Right Primary Button actions from your Input Action Asset
/// in the Inspector.
/// </summary>
[RequireComponent(typeof(Renderer))]
public class PrimaryButtonColorChange : MonoBehaviour
{
    [Header("Input Action References")]
    [SerializeField] private InputActionReference leftPrimaryButton;
    [SerializeField] private InputActionReference rightPrimaryButton;

    [Header("Colours")]
    [SerializeField] private Color colorA = Color.blue;
    [SerializeField] private Color colorB = Color.red;

    private Renderer _rend;
    private bool _toggled;

    void Awake()
    {
        _rend = GetComponent<Renderer>();
        _rend.material.color = colorA;
    }

    void OnEnable()
    {
        Enable(leftPrimaryButton);
        Enable(rightPrimaryButton);
    }

    void OnDisable()
    {
        Disable(leftPrimaryButton);
        Disable(rightPrimaryButton);
    }

    private void Enable(InputActionReference r)
    {
        if (r == null) return;
        r.action.Enable();
        r.action.performed += ToggleColor;
    }

    private void Disable(InputActionReference r)
    {
        if (r == null) return;
        r.action.performed -= ToggleColor;
    }

    private void ToggleColor(InputAction.CallbackContext ctx)
    {
        _toggled = !_toggled;
        _rend.material.color = _toggled ? colorB : colorA;
    }
}
