using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

/// <summary>
/// Task 4 — Visual highlight when a controller is within reach.
/// Attach to any XR Grab Interactable object.
/// Changes the material colour on hover enter / exit.
///
/// NOTE: _originalColor is captured at hover-enter time (not Awake) so it
/// always reflects the object's CURRENT colour — even after a primary-button
/// colour toggle — regardless of MonoBehaviour execution order.
/// </summary>
[RequireComponent(typeof(Renderer))]
[RequireComponent(typeof(XRGrabInteractable))]
public class HoverHighlight : MonoBehaviour
{
    [Header("Highlight Colour")]
    [SerializeField] private Color hoverColor = Color.yellow;

    private Renderer _rend;
    private Color _preHoverColor;          // saved just before applying the highlight
    private XRGrabInteractable _interactable;

    void Awake()
    {
        _rend         = GetComponent<Renderer>();
        _interactable = GetComponent<XRGrabInteractable>();
    }

    void OnEnable()
    {
        _interactable.hoverEntered.AddListener(OnHoverEntered);
        _interactable.hoverExited.AddListener(OnHoverExited);
    }

    void OnDisable()
    {
        _interactable.hoverEntered.RemoveListener(OnHoverEntered);
        _interactable.hoverExited.RemoveListener(OnHoverExited);
    }

    private void OnHoverEntered(HoverEnterEventArgs args)
    {
        _preHoverColor = _rend.material.color;   // snapshot the current colour
        _rend.material.color = hoverColor;
    }

    private void OnHoverExited(HoverExitEventArgs args)
    {
        _rend.material.color = _preHoverColor;   // restore whatever it was before hover
    }
}
