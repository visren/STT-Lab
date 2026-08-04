# Dependency layers for STT Lab
#
#   base.txt       core library + tests
#   ml.txt         STT / training (torch installed separately in Docker)
#   research.txt   Jupyter notebook UI
#   dictation.txt  local hotkey app
#   model-lab.txt  Docker compute image (base + ml)
#   ci.txt         fast CI (base only)
#
# Full local:  pip install -r requirements.txt
# CI:          pip install -r requirements/ci.txt
# model-lab:   see envs/model-lab/Dockerfile
