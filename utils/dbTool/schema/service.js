const mongoose = require('mongoose')

const serviceSchema = mongoose.Schema(
  {
    name: String,
    used_count: Number
  },
  { versionKey: false }
)
serviceSchema.set('collection', 'service')
exports.ServiceDB = mongoose.model('service', serviceSchema)
