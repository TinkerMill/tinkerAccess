use super::device;
use super::device_access;
use super::user;
use sea_orm::entity::prelude::*;

pub struct UserToDevice;
impl Linked for UserToDevice {
    type FromEntity = user::Entity;

    type ToEntity = device::Entity;

    fn link(&self) -> Vec<RelationDef> {
        vec![
            device_access::Relation::User.def().rev(),
            device_access::Relation::Device.def(),
        ]
    }
}

pub struct DeviceToUser;
impl Linked for DeviceToUser {
    type FromEntity = device::Entity;

    type ToEntity = user::Entity;

    fn link(&self) -> Vec<RelationDef> {
        vec![
            device_access::Relation::Device.def().rev(),
            device_access::Relation::User.def(),
        ]
    }
}
