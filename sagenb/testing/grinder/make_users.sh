for i in {1..50} 
do
    curl -d username=test$i localhost:8000/adduser
done
