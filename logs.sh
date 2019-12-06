

pod=$(kubectl get pod --selector app=rest --output name)
name=$(basename "$pod")

kubectl exec -it $name -- python3 logs.py "#"