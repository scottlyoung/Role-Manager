
pod=$(kubectl get pod --selector app=redis --output name)
name=$(basename "$pod")

kubectl exec -it $name -- redis-cli