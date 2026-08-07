# Migration from ansible-collection-azimuth-ops to flux

The Ansible role does the following:

- Makes a namespace
- Almost always (by default) deploys a CA configmap
- Can combine any CAs found on the Ansible host into the bundle
- The system-trust role makes the bundle
- Deploys cert-manager and mounts the bundle
- Creates a ClusterIssuer (by default for letsencrypt)
- Configures an EAB if the variables are set in the same issuer
- Registers an ingress annotation for the ClusterIssuer

Changes for the Flux way:

- trust-manager deploys the configmap bundle (by default it can get the default set)
- cert-manager always mounts the above configmap
- Always create a letsencrypt ClusterIssuer (if users want some EAB thing let them make a new issuer)
- How to manage the annotation for the new issuer - set it in static azimuth config
- If EAB secrets are needed they should be added by user in the `secrets` artifact

Need a way to be able to smoothly update the trust-manager bundle, maybe if it watches for secrets with the right label and no secrets exist thats fine?
Or they can override `extraObjects` and its a list so no merging?

Need to set the dependency between the prom-stack release and this so serviceMonitors work.
